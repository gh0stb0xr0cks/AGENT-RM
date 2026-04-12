"""Embeddings et chunking pour le RAG EBIOS RM."""

from rag.embeddings.embedding_config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_COLLECTION_NAME,
    CHROMA_PERSIST_DIR,
    DOCUMENT_SOURCES,
    EMBEDDING_BATCH_SIZE,
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    HYBRID_ALPHA,
    HYBRID_WEIGHTS,
    MAX_CONTEXT,
    METADATA_SCHEMA,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    RETRIEVAL_K,
    SEPARATORS,
    SIMILARITY_THRESHOLD,
)
from rag.embeddings.openrouter_embeddings import OpenRouterEmbeddings
from rag.embeddings.chunker import chunk_text, chunk_text_by_pages

__all__ = [
    # Config
    "CHUNK_OVERLAP",
    "CHUNK_SIZE",
    "CHROMA_COLLECTION_NAME",
    "CHROMA_PERSIST_DIR",
    "DOCUMENT_SOURCES",
    "EMBEDDING_BATCH_SIZE",
    "EMBEDDING_DIM",
    "EMBEDDING_MODEL",
    "HYBRID_ALPHA",
    "HYBRID_WEIGHTS",
    "MAX_CONTEXT",
    "METADATA_SCHEMA",
    "OPENROUTER_API_KEY",
    "OPENROUTER_BASE_URL",
    "RETRIEVAL_K",
    "SEPARATORS",
    "SIMILARITY_THRESHOLD",
    # Classes et fonctions
    "OpenRouterEmbeddings",
    "chunk_text",
    "chunk_text_by_pages",
]
