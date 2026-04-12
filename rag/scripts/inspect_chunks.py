#!/usr/bin/env python3
"""
Script d'inspection des chunks indexés dans ChromaDB.
Outil de debug pour vérifier le contenu et les métadonnées des chunks.
"""

import argparse
import logging
import sys
from pathlib import Path

import chromadb
from chromadb.config import Settings

# Assurer l'accès au projet racine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from rag.embeddings.embedding_config import (
    ATELIER_VALUES,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    SOURCE_VALUES,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def inspect_chunks(
    persist_dir: str = CHROMA_PERSIST_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
    atelier: str = None,
    source: str = None,
    doc_id: str = None,
    limit: int = 10,
    show_content: bool = False,
    stats_only: bool = False,
) -> None:
    """Affiche les chunks indexés avec leurs métadonnées.

    Args:
        persist_dir: Répertoire ChromaDB.
        collection_name: Nom de la collection.
        atelier: Filtre par atelier.
        source: Filtre par source.
        doc_id: Filtre par document ID.
        limit: Nombre max de chunks à afficher.
        show_content: Afficher le contenu des chunks.
        stats_only: N'afficher que les statistiques.
    """
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        logger.error("Collection '%s' introuvable", collection_name)
        sys.exit(1)

    total_count = collection.count()
    logger.info("Collection '%s' : %d chunks indexes", collection_name, total_count)

    # Statistiques globales
    if stats_only or not (atelier or source or doc_id):
        _print_stats(collection, total_count)

    if stats_only:
        return

    # Construire le filtre
    where_clause = {}
    if atelier:
        where_clause["atelier"] = atelier
    if source:
        where_clause["source"] = source
    if doc_id:
        where_clause["doc_id"] = doc_id

    if where_clause:
        logger.info("Filtres: %s", where_clause)

    # Récupérer les chunks
    results = collection.get(
        where=where_clause if where_clause else None,
        limit=limit,
        include=["documents", "metadatas"],
    )

    if not results["ids"]:
        logger.info("Aucun chunk trouve avec ces filtres")
        return

    logger.info("Affichage de %d chunks:\n", len(results["ids"]))

    for i, (chunk_id, doc, meta) in enumerate(
        zip(results["ids"], results["documents"], results["metadatas"])
    ):
        print(f"--- Chunk {i + 1} ---")
        print(f"ID: {chunk_id}")
        print(
            f"Atelier: {meta.get('atelier', 'N/A')} | "
            f"Type: {meta.get('type', 'N/A')} | "
            f"Source: {meta.get('source', 'N/A')}"
        )
        print(
            f"Document: {meta.get('doc_id', 'N/A')} | "
            f"Page: {meta.get('page', 'N/A')} | "
            f"Secteur: {meta.get('secteur', 'N/A')}"
        )
        print(f"Longueur: {len(doc)} chars")

        if show_content:
            preview = doc[:500] + "..." if len(doc) > 500 else doc
            print(f"Contenu:\n{preview}")

        print()


def _print_stats(collection, total_count: int) -> None:
    """Affiche les statistiques de la collection."""
    if total_count == 0:
        return

    # Récupérer toutes les métadonnées
    all_data = collection.get(
        limit=total_count,
        include=["metadatas"],
    )

    if not all_data["metadatas"]:
        return

    # Compter par atelier
    atelier_counts: dict[str, int] = {}
    source_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    doc_counts: dict[str, int] = {}

    for meta in all_data["metadatas"]:
        atelier = meta.get("atelier", "N/A")
        atelier_counts[atelier] = atelier_counts.get(atelier, 0) + 1

        source = meta.get("source", "N/A")
        source_counts[source] = source_counts.get(source, 0) + 1

        doc_type = meta.get("type", "N/A")
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

        doc_id = meta.get("doc_id", "N/A")
        doc_counts[doc_id] = doc_counts.get(doc_id, 0) + 1

    print("\n=== Statistiques ===\n")

    print("Par atelier:")
    for atelier in sorted(atelier_counts.keys()):
        print(f"  {atelier}: {atelier_counts[atelier]} chunks")

    print("\nPar source:")
    for source in sorted(source_counts.keys()):
        print(f"  {source}: {source_counts[source]} chunks")

    print("\nPar type:")
    for doc_type in sorted(type_counts.keys()):
        print(f"  {doc_type}: {type_counts[doc_type]} chunks")

    print("\nPar document:")
    for doc_id in sorted(doc_counts.keys()):
        print(f"  {doc_id}: {doc_counts[doc_id]} chunks")

    print()


def main():
    parser = argparse.ArgumentParser(description="Inspecte les chunks ChromaDB EBIOS RM")
    parser.add_argument("--persist-dir", default=CHROMA_PERSIST_DIR)
    parser.add_argument("--collection", default=CHROMA_COLLECTION_NAME)
    parser.add_argument(
        "--atelier",
        choices=ATELIER_VALUES,
        help="Filtrer par atelier",
    )
    parser.add_argument(
        "--source",
        choices=SOURCE_VALUES,
        help="Filtrer par source",
    )
    parser.add_argument("--doc-id", help="Filtrer par document ID")
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Nombre max de chunks a afficher",
    )
    parser.add_argument(
        "--show-content",
        action="store_true",
        help="Afficher le contenu des chunks",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Afficher uniquement les statistiques",
    )

    args = parser.parse_args()

    inspect_chunks(
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        atelier=args.atelier,
        source=args.source,
        doc_id=args.doc_id,
        limit=args.limit,
        show_content=args.show_content,
        stats_only=args.stats,
    )


if __name__ == "__main__":
    main()
