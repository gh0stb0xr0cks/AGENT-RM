"""
Configuration des embeddings et du RAG pour EBIOS RM.
Paramètres alignés sur la spécification AGENTS.md du module rag/.
"""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# ── Modèle d'embedding ──────────────────────────────────────────────────────
# Spécification : intfloat/multilingual-e5-base via OpenRouter
EMBEDDING_MODEL: str = os.getenv("OPENROUTER_EMBED_MODEL", "intfloat/multilingual-e5-base")
EMBEDDING_DIM: int = 768
MAX_CONTEXT: int = 512  # tokens

# ── OpenRouter API ───────────────────────────────────────────────────────────
OPENROUTER_API_KEY: Optional[str] = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")

# ── Paramètres de chunking ───────────────────────────────────────────────────
# Token-aware chunking avec respect des frontières de paragraphes
CHUNK_SIZE: int = 512  # tokens (~380 mots)
CHUNK_OVERLAP: int = 64  # continuité inter-chunks (listes EBIOS)
SEPARATORS: list[str] = ["\n\n", "\n", ".", " "]  # respect frontières paragraphes

# ── Valeurs de métadonnées autorisées ────────────────────────────────────────
ATELIER_VALUES: list[str] = ["A1", "A2", "A3", "A4", "A5", "all"]
TYPE_VALUES: list[str] = ["guide", "fiche", "exemple", "threat", "matrice"]
SOURCE_VALUES: list[str] = ["ANSSI", "ClubEBIOS", "MITRE", "synth"]
SECTEUR_VALUES: list[str] = ["sante", "industrie", "collectivite", "all"]
ETAPE_VALUES: list[str] = ["A", "B", "C", "D", "all"]

# ── Paramètres de retrieval par atelier ──────────────────────────────────────
RETRIEVAL_K: dict[str, int] = {
    "A1": 5,  # Termes précis, chunks courts suffisants
    "A2": 6,  # Profils SR/OV + cartographie sources de risque
    "A3": 7,  # Scénarios stratégiques + écosystème
    "A4": 8,  # Modes opératoires + MITRE ATT&CK
    "A5": 6,  # Plan traitement + exemples mesures
}

SIMILARITY_THRESHOLD: float = 0.75  # Cosine similarity minimale
HYBRID_ALPHA: float = 0.25  # Pondération: 0.25 * semantic + 0.75 * BM25
HYBRID_WEIGHTS: tuple[float, float] = (0.7, 0.3)  # EnsembleRetriever weights

# ── ChromaDB ─────────────────────────────────────────────────────────────────
CHROMA_PERSIST_DIR: str = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")
CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "ebios_rm_corpus")

# ── Schéma de métadonnées ChromaDB ───────────────────────────────────────────
# Chaque chunk DOIT avoir ces champs pour le filtrage par atelier.
METADATA_SCHEMA: dict[str, type] = {
    "atelier": str,  # A1|A2|A3|A4|A5|all
    "type": str,  # guide|fiche|exemple|threat|matrice
    "source": str,  # ANSSI|ClubEBIOS|MITRE|synth
    "secteur": str,  # sante|industrie|collectivite|all
    "etape": str,  # A|B|C|D|all
    "page": int,  # numéro de page source (traçabilité)
    "doc_id": str,  # identifiant document source
}

# ── Sources documentaires à indexer ──────────────────────────────────────────
# Mapping des fichiers vers leurs métadonnées par défaut
DOCUMENT_SOURCES: dict[str, dict] = {
    "guide_ebios_rm_2024.pdf": {
        "atelier": "all",
        "type": "guide",
        "source": "ANSSI",
        "secteur": "all",
        "etape": "all",
    },
    "fiches_methodes.pdf": {
        "atelier": "all",
        "type": "fiche",
        "source": "ANSSI",
        "secteur": "all",
        "etape": "all",
    },
    "matrice_rapport_sortie.pdf": {
        "atelier": "all",
        "type": "matrice",
        "source": "ClubEBIOS",
        "secteur": "all",
        "etape": "all",
    },
    "TTPs_EBIOS_RM_200.csv": {
        "atelier": "A4",
        "type": "threat",
        "source": "MITRE",
        "secteur": "all",
        "etape": "all",
    },
}

# ── Batch processing ─────────────────────────────────────────────────────────
EMBEDDING_BATCH_SIZE: int = 100  # Chunks par batch d'embedding
