"""
Chunking token-aware avec respect des frontières de paragraphes.
Conforme à la spécification AGENTS.md du module rag/ :
- CHUNK_SIZE = 512 tokens (~380 mots)
- CHUNK_OVERLAP = 64 tokens
- SEPARATORS = ["\\n\\n", "\\n", ".", " "]
"""

import logging
import re
from typing import Optional

from rag.embeddings.embedding_config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    SEPARATORS,
)

logger = logging.getLogger(__name__)

# Ratio moyen caractères/token pour le français (~4.5 chars/token)
CHARS_PER_TOKEN: float = 4.5


def estimate_tokens(text: str) -> int:
    """Estime le nombre de tokens dans un texte français.

    Utilise un ratio chars/token de ~4.5 pour le français.
    Plus précis qu'un simple len(text) pour le chunking token-aware.
    """
    return max(1, int(len(text) / CHARS_PER_TOKEN))


def _find_split_point(text: str, max_chars: int) -> int:
    """Trouve le meilleur point de coupure en respectant les séparateurs.

    Parcourt les séparateurs par ordre de priorité (paragraphe > ligne > phrase > mot)
    et retourne la position de la dernière occurrence avant max_chars.
    """
    if len(text) <= max_chars:
        return len(text)

    # Chercher le meilleur séparateur dans la zone de coupure
    for separator in SEPARATORS:
        # Chercher la dernière occurrence du séparateur avant la limite
        idx = text.rfind(separator, 0, max_chars)
        if idx > max_chars * 0.3:  # Au moins 30% du chunk rempli
            return idx + len(separator)

    # Fallback : couper au dernier espace avant la limite
    space_idx = text.rfind(" ", 0, max_chars)
    if space_idx > 0:
        return space_idx + 1

    # Dernier recours : couper à max_chars
    return max_chars


def chunk_text(
    text: str,
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[tuple[str, dict]]:
    """Découpe un texte en chunks token-aware avec overlap.

    Args:
        text: Texte source à découper.
        metadata: Métadonnées de base à copier sur chaque chunk.
        chunk_size: Taille cible en tokens (par défaut CHUNK_SIZE=512).
        chunk_overlap: Overlap en tokens (par défaut CHUNK_OVERLAP=64).

    Returns:
        Liste de tuples (chunk_text, chunk_metadata).
        Chaque metadata contient un champ 'page' mis à jour si possible.
    """
    if not text or not text.strip():
        return []

    # Nettoyer le texte
    text = _clean_text(text)

    # Convertir les tailles token en caractères approximatifs
    max_chars = int(chunk_size * CHARS_PER_TOKEN)
    overlap_chars = int(chunk_overlap * CHARS_PER_TOKEN)

    chunks = []
    start = 0
    text_len = len(text)
    chunk_idx = 0

    while start < text_len:
        # Trouver le point de coupure optimal
        remaining = text[start:]
        split_point = _find_split_point(remaining, max_chars)

        chunk_content = remaining[:split_point].strip()

        if not chunk_content:
            start += max_chars
            continue

        # Créer les métadonnées du chunk
        chunk_meta = metadata.copy()
        chunk_meta["chunk_index"] = chunk_idx

        # Estimer les tokens du chunk
        estimated_tokens = estimate_tokens(chunk_content)
        chunk_meta["estimated_tokens"] = estimated_tokens

        chunks.append((chunk_content, chunk_meta))
        chunk_idx += 1

        # Si le chunk couvre tout le texte restant, on a fini
        if split_point >= len(remaining):
            break

        # Avancer avec overlap (mais au moins 10% du max_chars pour éviter boucle)
        min_advance = max(int(max_chars * 0.1), 1)
        advance = max(split_point - overlap_chars, min_advance)
        start += advance

    logger.debug(
        "Texte découpé en %d chunks (source: %s)",
        len(chunks),
        metadata.get("doc_id", "unknown"),
    )
    return chunks


def chunk_text_by_pages(
    pages: list[tuple[str, int]],
    metadata: dict,
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> list[tuple[str, dict]]:
    """Découpe un document page par page en préservant les numéros de page.

    Args:
        pages: Liste de tuples (page_text, page_number).
        metadata: Métadonnées de base du document.
        chunk_size: Taille cible en tokens.
        chunk_overlap: Overlap en tokens.

    Returns:
        Liste de tuples (chunk_text, chunk_metadata) avec page exacte.
    """
    all_chunks = []

    for page_text, page_num in pages:
        if not page_text or not page_text.strip():
            continue

        page_meta = metadata.copy()
        page_meta["page"] = page_num

        page_chunks = chunk_text(
            page_text,
            page_meta,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        all_chunks.extend(page_chunks)

    return all_chunks


def _clean_text(text: str) -> str:
    """Nettoie le texte extrait de PDF.

    - Normalise les espaces multiples
    - Supprime les lignes vides excessives
    - Préserve la structure paragraphe/ligne
    """
    # Normaliser les fins de ligne Windows
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Réduire les espaces multiples (mais pas les newlines)
    text = re.sub(r"[ \t]+", " ", text)

    # Réduire plus de 2 lignes vides consécutives à 2
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Supprimer les espaces en début/fin de ligne
    lines = [line.strip() for line in text.split("\n")]
    text = "\n".join(lines)

    return text.strip()
