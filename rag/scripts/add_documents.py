#!/usr/bin/env python3
"""
Script d'ajout incrémental de documents à l'index ChromaDB.
Supporte PDF, TXT et CSV.
"""

import argparse
import csv
import logging
import os
import sys
from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

# Assurer l'accès au projet racine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rag.embeddings.embedding_config import (
    ATELIER_VALUES,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
    SECTEUR_VALUES,
    SOURCE_VALUES,
    TYPE_VALUES,
    ETAPE_VALUES,
)
from rag.embeddings.openrouter_embeddings import OpenRouterEmbeddings
from rag.embeddings.chunker import chunk_text, chunk_text_by_pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def extract_text_from_file(
    file_path: Path,
) -> Optional[list[tuple[str, int]]]:
    """Extrait le texte d'un fichier (PDF, TXT, CSV).

    Returns:
        Pour PDF : liste de (page_text, page_number).
        Pour TXT/CSV : liste avec un seul élément (full_text, 1).
        None si erreur.
    """
    suffix = file_path.suffix.lower()

    if suffix == ".pdf":
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append((text, i + 1))
            return pages if pages else None
        except ImportError:
            logger.error("pypdf non installe. Installer : pip install pypdf")
            return None
        except Exception as e:
            logger.error("Erreur lecture PDF %s: %s", file_path.name, e)
            return None

    elif suffix == ".txt":
        try:
            text = file_path.read_text(encoding="utf-8")
            return [(text, 1)] if text.strip() else None
        except Exception as e:
            logger.error("Erreur lecture TXT %s: %s", file_path.name, e)
            return None

    elif suffix == ".csv":
        try:
            parts = []
            with open(file_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    line_parts = []
                    for key, value in row.items():
                        if value and value.strip():
                            line_parts.append(f"{key}: {value.strip()}")
                    if line_parts:
                        parts.append("\n".join(line_parts))
            text = "\n\n".join(parts)
            return [(text, 1)] if text.strip() else None
        except Exception as e:
            logger.error("Erreur lecture CSV %s: %s", file_path.name, e)
            return None

    else:
        logger.warning("Format non supporte: %s", suffix)
        return None


def add_documents(
    file_paths: list[Path],
    atelier: str = "all",
    doc_type: str = "guide",
    source: str = "synth",
    secteur: str = "all",
    etape: str = "all",
    persist_dir: str = CHROMA_PERSIST_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> int:
    """Ajoute des documents à l'index ChromaDB existant.

    Args:
        file_paths: Chemins des fichiers à ajouter.
        atelier: Atelier associé (A1-A5 ou all).
        doc_type: Type de document (guide, fiche, exemple, threat, matrice).
        source: Source du document (ANSSI, ClubEBIOS, MITRE, synth).
        secteur: Secteur (sante, industrie, collectivite, all).
        etape: Etape (A, B, C, D, all).
        persist_dir: Répertoire ChromaDB.
        collection_name: Nom de la collection.

    Returns:
        Nombre de chunks ajoutés.
    """
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        logger.error(
            "Collection '%s' introuvable. Executer build_index.py d'abord.",
            collection_name,
        )
        sys.exit(1)

    logger.info("Ajout de %d document(s)...", len(file_paths))
    embedder = OpenRouterEmbeddings()

    all_chunks: list[tuple[str, dict]] = []

    for file_path in file_paths:
        logger.info("  Document: %s", file_path.name)

        pages = extract_text_from_file(file_path)
        if not pages:
            logger.warning("  Aucun texte extrait, skip")
            continue

        metadata = {
            "doc_id": file_path.stem,
            "atelier": atelier,
            "type": doc_type,
            "source": source,
            "secteur": secteur,
            "etape": etape,
        }

        if file_path.suffix.lower() == ".pdf":
            chunks = chunk_text_by_pages(pages, metadata)
        else:
            metadata["page"] = 1
            text = pages[0][0]
            chunks = chunk_text(text, metadata)

        all_chunks.extend(chunks)
        logger.info("    -> %d chunks", len(chunks))

    if not all_chunks:
        logger.error("Aucun chunk a ajouter")
        return 0

    texts = [chunk[0] for chunk in all_chunks]
    metadatas = [chunk[1] for chunk in all_chunks]

    logger.info("Generation embeddings (%s)...", EMBEDDING_MODEL)
    embeddings = embedder(texts)

    base_count = collection.count()
    ids = [f"add_{meta['doc_id']}_p{meta.get('page', 0)}_c{i}" for i, meta in enumerate(metadatas)]

    # Upsert par batch
    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch_ids = ids[i : i + EMBEDDING_BATCH_SIZE]
        batch_docs = texts[i : i + EMBEDDING_BATCH_SIZE]
        batch_embeddings = embeddings[i : i + EMBEDDING_BATCH_SIZE]
        batch_metas = metadatas[i : i + EMBEDDING_BATCH_SIZE]

        collection.upsert(
            ids=batch_ids,
            documents=batch_docs,
            embeddings=batch_embeddings,
            metadatas=batch_metas,
        )

    added = collection.count() - base_count
    logger.info(
        "%d chunks ajoutes (total: %d -> %d)",
        len(all_chunks),
        base_count,
        collection.count(),
    )
    return len(all_chunks)


def main():
    parser = argparse.ArgumentParser(description="Ajoute des documents a l'index ChromaDB EBIOS RM")
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Fichiers a ajouter (PDF, TXT ou CSV)",
    )
    parser.add_argument(
        "--atelier",
        default="all",
        choices=ATELIER_VALUES,
        help="Atelier associe",
    )
    parser.add_argument(
        "--type",
        default="guide",
        choices=TYPE_VALUES,
        help="Type de document",
    )
    parser.add_argument(
        "--source",
        default="synth",
        choices=SOURCE_VALUES,
        help="Source du document",
    )
    parser.add_argument(
        "--secteur",
        default="all",
        choices=SECTEUR_VALUES,
        help="Secteur cible",
    )
    parser.add_argument(
        "--etape",
        default="all",
        choices=ETAPE_VALUES,
        help="Etape de la methode",
    )
    parser.add_argument("--persist-dir", default=CHROMA_PERSIST_DIR)
    parser.add_argument("--collection", default=CHROMA_COLLECTION_NAME)

    args = parser.parse_args()

    add_documents(
        file_paths=args.files,
        atelier=args.atelier,
        doc_type=args.type,
        source=args.source,
        secteur=args.secteur,
        etape=args.etape,
        persist_dir=args.persist_dir,
        collection_name=args.collection,
    )


if __name__ == "__main__":
    main()
