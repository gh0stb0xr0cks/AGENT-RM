"""
chunk_formatter.py — Normalisation des sorties d'atelier.

Formate la réponse brute du LLM pour l'affichage et l'export structuré.
"""

import re
from typing import Any, Optional


def format_atelier_output(
    answer: str,
    atelier: str,
    metadata: Optional[dict] = None,
) -> dict[str, Any]:
    """Normalise la sortie LLM d'un atelier pour affichage et export.

    Args:
        answer: Réponse brute du LLM.
        atelier: Identifiant de l'atelier (A1-A5).
        metadata: Métadonnées optionnelles (sources RAG, timestamps, etc.).

    Returns:
        Dictionnaire structuré avec la réponse formatée.
    """
    output = {
        "atelier": atelier,
        "answer": answer.strip(),
        "sections": _extract_sections(answer),
        "metadata": metadata or {},
    }

    # Extraire les éléments structurés si présents
    extracted = _extract_structured_elements(answer, atelier)
    if extracted:
        output["structured"] = extracted

    return output


def _extract_sections(text: str) -> list[dict[str, str]]:
    """Extrait les sections du texte (titres markdown).

    Returns:
        Liste de {"title": str, "content": str, "level": int}.
    """
    sections = []
    pattern = r"^(#{1,4})\s+(.+)$"
    lines = text.split("\n")

    current_section = None
    current_content = []

    for line in lines:
        match = re.match(pattern, line)
        if match:
            if current_section is not None:
                current_section["content"] = "\n".join(current_content).strip()
                sections.append(current_section)

            level = len(match.group(1))
            title = match.group(2).strip()
            current_section = {
                "title": title,
                "level": level,
                "content": "",
            }
            current_content = []
        elif current_section is not None:
            current_content.append(line)

    if current_section is not None:
        current_section["content"] = "\n".join(current_content).strip()
        sections.append(current_section)

    return sections


def _extract_structured_elements(text: str, atelier: str) -> Optional[dict[str, list[str]]]:
    """Extrait les éléments structurés spécifiques à chaque atelier.

    Returns:
        Dictionnaire des éléments extraits ou None.
    """
    elements = {}

    # Extraire les listes à puces
    bullet_items = re.findall(r"^[-*]\s+(.+)$", text, re.MULTILINE)
    if bullet_items:
        elements["items"] = bullet_items

    # Extraire les éléments numérotés
    numbered_items = re.findall(r"^\d+[.)]\s+(.+)$", text, re.MULTILINE)
    if numbered_items:
        elements["numbered_items"] = numbered_items

    return elements if elements else None
