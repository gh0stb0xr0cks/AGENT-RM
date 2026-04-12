#!/usr/bin/env python3
"""
Script de construction de l'index ChromaDB pour EBIOS RM.

Sources indexées (conformément à rag/AGENTS.md) :
1. docs/ebios/guide_ebios_rm_2024.pdf    -> atelier=all, source=ANSSI
2. docs/ebios/fiches_methodes.pdf        -> atelier=all, source=ANSSI
3. docs/ebios/matrice_rapport_sortie.pdf  -> atelier=all, source=ClubEBIOS
4. docs/ebios/TTPs_EBIOS_RM_200.csv      -> atelier=A4, source=MITRE
5. corpus/datasets/*.jsonl               -> atelier=*, source=synth
"""

import argparse
import csv
import json
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
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    DOCUMENT_SOURCES,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_MODEL,
)
from rag.embeddings.openrouter_embeddings import OpenRouterEmbeddings
from rag.embeddings.chunker import chunk_text, chunk_text_by_pages

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Extracteurs de documents ─────────────────────────────────────────────────


def extract_pdf_pages(pdf_path: Path) -> list[tuple[str, int]]:
    """Extrait le texte d'un PDF page par page.

    Returns:
        Liste de tuples (page_text, page_number) avec page_number 1-indexed.
    """
    try:
        from pypdf import PdfReader

        reader = PdfReader(str(pdf_path))
        pages = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append((text, i + 1))
        return pages
    except ImportError:
        logger.error("pypdf non installe. Installer avec : pip install pypdf")
        return []
    except Exception as e:
        logger.error("Erreur lecture %s: %s", pdf_path.name, e)
        return []


def extract_csv_rows(csv_path: Path) -> list[tuple[str, dict]]:
    """Extrait les lignes d'un fichier CSV MITRE ATT&CK.

    Chaque ligne est convertie en texte structuré avec les métadonnées MITRE.
    Returns:
        Liste de tuples (row_text, row_metadata).
    """
    rows = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Construire un texte structuré à partir des colonnes
                parts = []
                for key, value in row.items():
                    if value and value.strip():
                        parts.append(f"{key}: {value.strip()}")
                text = "\n".join(parts)

                if text.strip():
                    rows.append((text, {"csv_row": i + 1}))

        logger.info("  %d lignes extraites de %s", len(rows), csv_path.name)
    except Exception as e:
        logger.error("Erreur lecture CSV %s: %s", csv_path.name, e)

    return rows


def extract_jsonl_examples(jsonl_path: Path) -> list[tuple[str, dict]]:
    """Extrait les exemples d'un fichier JSONL du corpus synthétique.

    Chaque entrée JSONL est convertie en texte contextualisé.
    Returns:
        Liste de tuples (example_text, example_metadata).
    """
    examples = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    # Extraire le texte pertinent (format ChatML ou Q/A)
                    text = _format_jsonl_entry(entry)
                    if text:
                        meta = {
                            "jsonl_index": i,
                            "jsonl_file": jsonl_path.stem,
                        }
                        # Extraire l'atelier si présent dans l'entrée
                        if "atelier" in entry:
                            meta["atelier_hint"] = entry["atelier"]
                        examples.append((text, meta))
                except json.JSONDecodeError:
                    continue

        logger.info("  %d exemples extraits de %s", len(examples), jsonl_path.name)
    except Exception as e:
        logger.error("Erreur lecture JSONL %s: %s", jsonl_path.name, e)

    return examples


def _format_jsonl_entry(entry: dict) -> Optional[str]:
    """Formate une entrée JSONL en texte indexable."""
    # Format ChatML (messages)
    if "messages" in entry:
        parts = []
        for msg in entry["messages"]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if content and role in ("user", "assistant", "system"):
                parts.append(f"[{role}] {content}")
        return "\n".join(parts) if parts else None

    # Format Q/A simple
    if "question" in entry and "answer" in entry:
        return f"Question: {entry['question']}\nReponse: {entry['answer']}"

    # Format instruction/output
    if "instruction" in entry:
        text = f"Instruction: {entry['instruction']}"
        if "output" in entry:
            text += f"\nReponse: {entry['output']}"
        return text

    return None


# ── Chargement des sources ───────────────────────────────────────────────────


def load_pdf_documents(
    docs_dir: Path,
) -> list[tuple[str, dict]]:
    """Charge et chunke tous les PDFs du répertoire docs/ebios/.

    Utilise DOCUMENT_SOURCES pour associer les métadonnées correctes.
    Découpe page par page pour préserver le numéro de page réel.
    """
    all_chunks = []

    for pdf_file in sorted(docs_dir.glob("*.pdf")):
        filename = pdf_file.name
        source_meta = DOCUMENT_SOURCES.get(filename)

        if source_meta is None:
            logger.warning("PDF non reconnu (pas dans DOCUMENT_SOURCES): %s", filename)
            source_meta = {
                "atelier": "all",
                "type": "guide",
                "source": "ANSSI",
                "secteur": "all",
                "etape": "all",
            }

        metadata = {
            "doc_id": pdf_file.stem,
            **source_meta,
        }

        logger.info("  Extraction PDF: %s (source=%s)", filename, metadata["source"])
        pages = extract_pdf_pages(pdf_file)

        if not pages:
            logger.warning("  Aucun texte extrait de %s", filename)
            continue

        chunks = chunk_text_by_pages(pages, metadata)
        all_chunks.extend(chunks)
        logger.info("    -> %d chunks (%d pages)", len(chunks), len(pages))

    return all_chunks


def load_csv_documents(docs_dir: Path) -> list[tuple[str, dict]]:
    """Charge et chunke les fichiers CSV (MITRE ATT&CK)."""
    all_chunks = []

    for csv_file in sorted(docs_dir.glob("*.csv")):
        filename = csv_file.name
        source_meta = DOCUMENT_SOURCES.get(filename)

        if source_meta is None:
            logger.warning("CSV non reconnu: %s", filename)
            continue

        metadata = {
            "doc_id": csv_file.stem,
            "page": 1,
            **source_meta,
        }

        logger.info("  Extraction CSV: %s (source=%s)", filename, metadata["source"])
        rows = extract_csv_rows(csv_file)

        if not rows:
            logger.warning("  Aucune donnee extraite de %s", filename)
            continue

        # Pour le CSV, chaque ligne peut devenir un chunk directement
        # ou être regroupée si trop petite
        for row_text, row_meta in rows:
            chunk_meta = metadata.copy()
            chunk_meta["page"] = row_meta.get("csv_row", 1)
            # Les lignes CSV sont généralement courtes -> un chunk par ligne
            chunks = chunk_text(row_text, chunk_meta)
            all_chunks.extend(chunks)

        logger.info("    -> %d chunks", len(all_chunks))

    return all_chunks


def load_synthetic_corpus(corpus_dir: Path) -> list[tuple[str, dict]]:
    """Charge et chunke le corpus synthétique (JSONL)."""
    all_chunks = []
    datasets_dir = corpus_dir / "datasets"

    if not datasets_dir.exists():
        logger.info("  Repertoire corpus/datasets/ introuvable, skip")
        return all_chunks

    jsonl_files = list(datasets_dir.glob("*.jsonl"))
    if not jsonl_files:
        logger.info("  Aucun fichier .jsonl dans corpus/datasets/, skip")
        return all_chunks

    for jsonl_file in sorted(jsonl_files):
        metadata = {
            "doc_id": jsonl_file.stem,
            "atelier": "all",
            "type": "exemple",
            "source": "synth",
            "secteur": "all",
            "etape": "all",
            "page": 1,
        }

        logger.info("  Extraction JSONL: %s", jsonl_file.name)
        examples = extract_jsonl_examples(jsonl_file)

        for example_text, example_meta in examples:
            chunk_meta = metadata.copy()
            # Utiliser l'atelier hint si disponible
            if "atelier_hint" in example_meta:
                chunk_meta["atelier"] = example_meta["atelier_hint"]
            chunk_meta["page"] = example_meta.get("jsonl_index", 1)

            chunks = chunk_text(example_text, chunk_meta)
            all_chunks.extend(chunks)

        logger.info("    -> %d chunks", len(all_chunks))

    return all_chunks


# ── Construction de l'index ──────────────────────────────────────────────────


def build_index(
    reset: bool = False,
    all_sources: bool = True,
    persist_dir: str = CHROMA_PERSIST_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
) -> int:
    """Construit l'index ChromaDB complet.

    Args:
        reset: Supprimer l'index existant avant reconstruction.
        all_sources: Indexer toutes les sources (PDF + CSV + JSONL).
        persist_dir: Répertoire de persistence ChromaDB.
        collection_name: Nom de la collection.

    Returns:
        Nombre total de chunks indexés.
    """
    project_root = Path(__file__).parent.parent.parent
    docs_dir = project_root / "docs" / "ebios"
    corpus_dir = project_root / "corpus"

    if not docs_dir.exists():
        logger.error("Repertoire %s introuvable", docs_dir)
        sys.exit(1)

    os.makedirs(persist_dir, exist_ok=True)

    # Initialiser ChromaDB
    logger.info("Initialisation ChromaDB (persist: %s)", persist_dir)
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    if reset:
        logger.info("Suppression collection '%s'", collection_name)
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "Corpus EBIOS RM - Methode ANSSI 2024",
            "embedding_model": EMBEDDING_MODEL,
        },
    )

    # Charger et chunker toutes les sources
    logger.info("Chargement des documents...")

    all_chunks: list[tuple[str, dict]] = []

    # Source 1-3 : PDFs
    pdf_chunks = load_pdf_documents(docs_dir)
    all_chunks.extend(pdf_chunks)
    logger.info("PDFs: %d chunks", len(pdf_chunks))

    # Source 4 : CSV MITRE ATT&CK
    csv_chunks = load_csv_documents(docs_dir)
    all_chunks.extend(csv_chunks)
    logger.info("CSV MITRE: %d chunks", len(csv_chunks))

    # Source 5 : Corpus synthétique
    if all_sources:
        synth_chunks = load_synthetic_corpus(corpus_dir)
        all_chunks.extend(synth_chunks)
        logger.info("Corpus synthetique: %d chunks", len(synth_chunks))

    if not all_chunks:
        logger.error("Aucun chunk genere")
        sys.exit(1)

    logger.info("Total: %d chunks a indexer", len(all_chunks))

    # Générer les embeddings et indexer par batch
    logger.info("Generation embeddings (%s)...", EMBEDDING_MODEL)
    embedder = OpenRouterEmbeddings()

    texts = [chunk[0] for chunk in all_chunks]
    metadatas = [chunk[1] for chunk in all_chunks]

    # Valider et normaliser les métadonnées
    for meta in metadatas:
        _validate_metadata(meta)

    total_batches = (len(texts) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

    for i in range(0, len(texts), EMBEDDING_BATCH_SIZE):
        batch_texts = texts[i : i + EMBEDDING_BATCH_SIZE]
        batch_metas = metadatas[i : i + EMBEDDING_BATCH_SIZE]

        embeddings = embedder(batch_texts)
        ids = [
            f"{meta['doc_id']}_p{meta.get('page', 0)}_c{i + j}"
            for j, meta in enumerate(batch_metas)
        ]

        collection.upsert(
            ids=ids,
            documents=batch_texts,
            embeddings=embeddings,
            metadatas=batch_metas,
        )

        batch_num = i // EMBEDDING_BATCH_SIZE + 1
        logger.info("  Batch %d/%d indexe", batch_num, total_batches)

    total_count = collection.count()
    logger.info("Index construit: %d chunks", total_count)
    logger.info("  Collection: %s", collection_name)
    logger.info("  Persist: %s", persist_dir)

    return total_count


def _validate_metadata(meta: dict) -> None:
    """Valide et normalise les métadonnées d'un chunk.

    S'assure que tous les champs requis du schéma sont présents.
    """
    from rag.embeddings.embedding_config import (
        ATELIER_VALUES,
        TYPE_VALUES,
        SOURCE_VALUES,
        SECTEUR_VALUES,
        ETAPE_VALUES,
    )

    # Valeurs par défaut
    meta.setdefault("atelier", "all")
    meta.setdefault("type", "guide")
    meta.setdefault("source", "ANSSI")
    meta.setdefault("secteur", "all")
    meta.setdefault("etape", "all")
    meta.setdefault("page", 1)
    meta.setdefault("doc_id", "unknown")

    # Validation des valeurs
    if meta["atelier"] not in ATELIER_VALUES:
        logger.warning("Atelier invalide '%s', fallback 'all'", meta["atelier"])
        meta["atelier"] = "all"

    if meta["type"] not in TYPE_VALUES:
        logger.warning("Type invalide '%s', fallback 'guide'", meta["type"])
        meta["type"] = "guide"

    if meta["source"] not in SOURCE_VALUES:
        logger.warning("Source invalide '%s', fallback 'ANSSI'", meta["source"])
        meta["source"] = "ANSSI"

    if meta["secteur"] not in SECTEUR_VALUES:
        meta["secteur"] = "all"

    if meta["etape"] not in ETAPE_VALUES:
        meta["etape"] = "all"

    # Convertir page en int
    meta["page"] = int(meta.get("page", 1))

    # Supprimer les champs non-sérialisables pour ChromaDB
    for key in list(meta.keys()):
        if key not in ("atelier", "type", "source", "secteur", "etape", "page", "doc_id"):
            # ChromaDB n'accepte que str, int, float, bool
            if not isinstance(meta[key], (str, int, float, bool)):
                del meta[key]


# ── CLI ──────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Construit l'index ChromaDB EBIOS RM")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Supprime l'index existant avant reconstruction",
    )
    parser.add_argument(
        "--all-sources",
        action="store_true",
        default=True,
        help="Indexe toutes les sources (PDF + CSV + corpus synthetique)",
    )
    parser.add_argument(
        "--persist-dir",
        default=CHROMA_PERSIST_DIR,
        help="Repertoire de persistence ChromaDB",
    )
    parser.add_argument(
        "--collection",
        default=CHROMA_COLLECTION_NAME,
        help="Nom de la collection ChromaDB",
    )

    args = parser.parse_args()

    count = build_index(
        reset=args.reset,
        all_sources=args.all_sources,
        persist_dir=args.persist_dir,
        collection_name=args.collection,
    )

    logger.info("Termine avec %d chunks indexes", count)


if __name__ == "__main__":
    main()
