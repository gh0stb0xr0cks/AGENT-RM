"""
Client d'embeddings OpenRouter partagé pour le module RAG EBIOS RM.
Utilisé par build_index.py, add_documents.py et test_retrieval.py.
"""

import logging
from typing import Optional

import httpx

from rag.embeddings.embedding_config import (
    EMBEDDING_DIM,
    EMBEDDING_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    EMBEDDING_BATCH_SIZE,
)

logger = logging.getLogger(__name__)


class OpenRouterEmbeddings:
    """Client d'embeddings via l'API OpenRouter.

    Supporte le batching automatique pour les grands volumes de textes.
    Compatible avec le modèle intfloat/multilingual-e5-base (768 dims).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        self.model = model or EMBEDDING_MODEL
        self.api_key = api_key or OPENROUTER_API_KEY
        self.base_url = base_url or OPENROUTER_BASE_URL
        self.dimension = EMBEDDING_DIM
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "OPENROUTER_API_KEY non configurée. "
                "Définir la variable d'environnement ou passer api_key."
            )

    def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Envoie un batch de textes à l'API OpenRouter."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
        }

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/embeddings",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

        # Trier par index pour garantir l'ordre
        sorted_data = sorted(data["data"], key=lambda x: x["index"])
        return [item["embedding"] for item in sorted_data]

    def __call__(self, texts: list[str]) -> list[list[float]]:
        """Génère des embeddings pour une liste de textes.

        Gère automatiquement le batching si len(texts) > EMBEDDING_BATCH_SIZE.
        """
        if not texts:
            return []

        all_embeddings = []
        batch_size = EMBEDDING_BATCH_SIZE

        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            logger.debug(
                "Embedding batch %d/%d (%d textes)",
                i // batch_size + 1,
                (len(texts) + batch_size - 1) // batch_size,
                len(batch),
            )
            embeddings = self._embed_batch(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> list[float]:
        """Génère l'embedding pour un seul texte (interface LangChain)."""
        return self([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Génère les embeddings pour une liste de documents (interface LangChain)."""
        return self(texts)
