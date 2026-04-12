#!/usr/bin/env python3
"""
Script de test de la qualité du retrieval ChromaDB.
Exécute des requêtes de test par atelier et vérifie les scores hybrides.
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
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    HYBRID_ALPHA,
    RETRIEVAL_K,
    SIMILARITY_THRESHOLD,
)
from rag.embeddings.openrouter_embeddings import OpenRouterEmbeddings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# Tentative d'import BM25
try:
    from rank_bm25 import BM25Okapi

    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False
    logger.warning("rank-bm25 non installe, retrieval lexical desactive")


# ── Requêtes de test par atelier ─────────────────────────────────────────────
# Terminologie EBIOS RM 2024 stricte (pas de termes EBIOS 2010)

TEST_QUERIES: dict[str, list[str]] = {
    "A1": [
        "definition valeur metier",
        "sources de risque objectifs vises",
        "etape cartographie des biens supports",
    ],
    "A2": [
        "profil source de risque",
        "objectifs vises et scenarios de risque",
        "grille de cotation gravite vraisemblance",
    ],
    "A3": [
        "scenario de risque strategique",
        "ecosysteme numerique parties prenantes",
        "chemin d'attaque strategique",
    ],
    "A4": [
        "mode operatoire attaquant action elementaire",
        "mesures de securite existantes",
        "MITRE ATT&CK tactique technique",
    ],
    "A5": [
        "plan de traitement du risque",
        "mesures de securite a mettre en oeuvre",
        "risque residuel acceptation",
    ],
}


# ── Fonctions utilitaires ────────────────────────────────────────────────────


def normalize_score(score: float, min_score: float, max_score: float) -> float:
    """Normalise un score entre 0 et 1."""
    if max_score == min_score:
        return 1.0 if score > min_score else 0.0
    return (score - min_score) / (max_score - min_score)


def compute_bm25_scores(query: str, documents: list[str]) -> list[float]:
    """Calcule les scores BM25 normalisés pour une liste de documents."""
    if not BM25_AVAILABLE or not documents:
        return [0.0] * len(documents)

    tokenized_docs = [doc.lower().split() for doc in documents]
    bm25 = BM25Okapi(tokenized_docs)

    tokenized_query = query.lower().split()
    scores = bm25.get_scores(tokenized_query)

    if max(scores) == 0:
        return [0.0] * len(scores)

    return [normalize_score(s, min(scores), max(scores)) for s in scores]


def retrieve(
    query: str,
    collection,
    embedder: OpenRouterEmbeddings,
    atelier: str = "all",
    k: int = 5,
    hybrid_alpha: float = HYBRID_ALPHA,
) -> list[dict]:
    """Effectue une requête de retrieval hybride (sémantique + BM25).

    Args:
        query: Requête utilisateur.
        collection: Collection ChromaDB.
        embedder: Client d'embeddings.
        atelier: Filtre par atelier (ou "all").
        k: Nombre de résultats à retourner.
        hybrid_alpha: Pondération sémantique (1-alpha = BM25).

    Returns:
        Liste de résultats triés par score hybride décroissant.
    """
    query_embedding = embedder.embed_query(query)

    # Filtrage par atelier
    where_clause = None
    if atelier != "all":
        where_clause = {
            "$or": [
                {"atelier": {"$eq": atelier}},
                {"atelier": {"$eq": "all"}},
            ]
        }

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k * 2,  # Surcharger pour le re-ranking BM25
        where=where_clause,
        include=["documents", "metadatas", "distances"],
    )

    retrieved = []
    if not results["documents"] or not results["documents"][0]:
        return retrieved

    docs = results["documents"][0]
    bm25_scores = compute_bm25_scores(query, docs)

    for i, doc in enumerate(docs):
        distance = results["distances"][0][i]
        semantic_sim = max(0.0, 1 - distance)  # Clamp à 0

        keyword_score = bm25_scores[i]

        # Score hybride : alpha * sémantique + (1-alpha) * BM25
        hybrid_score = (hybrid_alpha * semantic_sim) + ((1 - hybrid_alpha) * keyword_score)

        retrieved.append(
            {
                "document": doc[:200],  # Preview
                "metadata": results["metadatas"][0][i],
                "similarity": hybrid_score,
                "semantic_sim": semantic_sim,
                "keyword_score": keyword_score,
                "distance": distance,
            }
        )

    retrieved.sort(key=lambda x: x["similarity"], reverse=True)
    return retrieved[:k]


# ── Exécution des tests ──────────────────────────────────────────────────────


def run_tests(
    persist_dir: str = CHROMA_PERSIST_DIR,
    collection_name: str = CHROMA_COLLECTION_NAME,
    verbose: bool = False,
) -> bool:
    """Exécute les tests de retrieval sur tous les ateliers.

    Returns:
        True si tous les tests passent, False sinon.
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

    total_chunks = collection.count()
    logger.info("Test retrieval sur '%s' (%d chunks)", collection_name, total_chunks)

    embedder = OpenRouterEmbeddings()

    all_passed = True
    total_queries = 0
    total_passed = 0

    for atelier, queries in TEST_QUERIES.items():
        k = RETRIEVAL_K.get(atelier, 5)
        logger.info("--- Atelier %s (k=%d) ---", atelier, k)

        for query in queries:
            total_queries += 1
            results = retrieve(
                query,
                collection,
                embedder,
                atelier="all",  # Tester sur tout le corpus
                k=k,
                hybrid_alpha=HYBRID_ALPHA,
            )

            if not results:
                logger.warning("  FAIL '%s' -> aucun resultat", query)
                all_passed = False
                continue

            above_threshold = [r for r in results if r["similarity"] >= SIMILARITY_THRESHOLD]

            if above_threshold:
                total_passed += 1
                status = "PASS"
            else:
                all_passed = False
                status = "FAIL"

            best = results[0]
            logger.info(
                "  %s '%s' -> hybrid=%.3f (sem=%.3f, bm25=%.3f)",
                status,
                query,
                best["similarity"],
                best["semantic_sim"],
                best["keyword_score"],
            )

            if verbose and results:
                for r in results[:3]:
                    logger.info(
                        "    [%s p.%s] %.3f : %s...",
                        r["metadata"].get("source", "?"),
                        r["metadata"].get("page", "?"),
                        r["similarity"],
                        r["document"][:80],
                    )

    logger.info("=" * 60)
    logger.info(
        "Resultats: %d/%d queries OK (seuil=%.2f, alpha=%.2f)",
        total_passed,
        total_queries,
        SIMILARITY_THRESHOLD,
        HYBRID_ALPHA,
    )

    if all_passed:
        logger.info("PASS - Tous les tests de retrieval passes")
    else:
        logger.warning("FAIL - Certains tests echoues")

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Teste la qualite du retrieval ChromaDB EBIOS RM")
    parser.add_argument("--persist-dir", default=CHROMA_PERSIST_DIR)
    parser.add_argument("--collection", default=CHROMA_COLLECTION_NAME)
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Affiche les details des resultats"
    )

    args = parser.parse_args()

    passed = run_tests(
        persist_dir=args.persist_dir,
        collection_name=args.collection,
        verbose=args.verbose,
    )

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
