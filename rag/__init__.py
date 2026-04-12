"""RAG module pour EBIOS RM - Base vectorielle ChromaDB avec embeddings OpenRouter."""

from rag.embeddings.embedding_config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    HYBRID_ALPHA,
    HYBRID_WEIGHTS,
    MAX_CONTEXT,
    RETRIEVAL_K,
    SIMILARITY_THRESHOLD,
)
from rag.embeddings.openrouter_embeddings import OpenRouterEmbeddings
from rag.embeddings.chunker import chunk_text, chunk_text_by_pages

__all__ = [
    # Configuration
    "CHUNK_OVERLAP",
    "CHUNK_SIZE",
    "CHROMA_COLLECTION_NAME",
    "CHROMA_PERSIST_DIR",
    "EMBEDDING_DIM",
    "EMBEDDING_MODEL",
    "HYBRID_ALPHA",
    "HYBRID_WEIGHTS",
    "MAX_CONTEXT",
    "RETRIEVAL_K",
    "SIMILARITY_THRESHOLD",
    # Classes et fonctions
    "OpenRouterEmbeddings",
    "chunk_text",
    "chunk_text_by_pages",
]
