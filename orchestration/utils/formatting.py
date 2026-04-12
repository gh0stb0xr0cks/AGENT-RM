"""
formatting.py — Formatage du contexte RAG pour injection dans les prompts.

Formate les documents récupérés par ChromaDB avec des références traçables :
[Réf.N — SOURCE p.PAGE]

Utilisé dans la chain LCEL : retriever | RunnableLambda(format_rag_context)
"""

from typing import Union


def format_rag_context(docs: Union[list, None]) -> str:
    """Formate les chunks RAG récupérés avec références de source.

    Compatible avec :
    - LangChain Documents (objects avec .page_content et .metadata)
    - Dictionnaires bruts (avec clés 'document'/'page_content' et 'metadata')

    Args:
        docs: Liste de documents LangChain ou dictionnaires.

    Returns:
        Contexte formaté avec références [Réf.N — SOURCE p.PAGE].
        Retourne une chaîne vide si aucun document.
    """
    if not docs:
        return ""

    formatted_parts = []

    for i, doc in enumerate(docs, start=1):
        # Extraire le contenu et les métadonnées
        content, metadata = _extract_doc_fields(doc)

        if not content:
            continue

        # Construire la référence
        source = metadata.get("source", "N/A")
        page = metadata.get("page", "?")
        doc_id = metadata.get("doc_id", "")
        atelier = metadata.get("atelier", "all")

        ref_label = f"[Ref.{i} -- {source} p.{page}]"

        # Ajouter l'indicateur d'atelier si spécifique
        if atelier != "all":
            ref_label = f"[Ref.{i} -- {source} p.{page} ({atelier})]"

        formatted_parts.append(f"{ref_label}\n{content.strip()}")

    if not formatted_parts:
        return ""

    return "\n\n---\n\n".join(formatted_parts)


def format_rag_context_compact(docs: Union[list, None]) -> str:
    """Version compacte du formatage RAG (pour contextes limités en tokens).

    Retourne un format plus court sans séparateurs visuels.
    """
    if not docs:
        return ""

    parts = []
    for i, doc in enumerate(docs, start=1):
        content, metadata = _extract_doc_fields(doc)
        if not content:
            continue

        source = metadata.get("source", "N/A")
        page = metadata.get("page", "?")

        # Tronquer le contenu si trop long (max 500 chars)
        truncated = content.strip()[:500]
        if len(content.strip()) > 500:
            truncated += "..."

        parts.append(f"[{i}|{source} p.{page}] {truncated}")

    return "\n".join(parts)


def _extract_doc_fields(doc) -> tuple[str, dict]:
    """Extrait le contenu et les métadonnées d'un document.

    Supporte les objets LangChain Document et les dictionnaires.

    Returns:
        Tuple (content, metadata).
    """
    # LangChain Document object
    if hasattr(doc, "page_content") and hasattr(doc, "metadata"):
        return doc.page_content, doc.metadata or {}

    # Dictionnaire avec 'page_content'
    if isinstance(doc, dict):
        content = doc.get("page_content", doc.get("document", ""))
        metadata = doc.get("metadata", {})
        return content, metadata

    # String brut
    if isinstance(doc, str):
        return doc, {}

    return "", {}
