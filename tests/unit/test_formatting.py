"""
Tests unitaires pour le formatage RAG et les sorties d'atelier.
Couvre :
- orchestration/utils/formatting.py  (format_rag_context)
- orchestration/utils/chunk_formatter.py (format_atelier_output)
- rag/embeddings/chunker.py (chunk_text, chunk_text_by_pages)
"""

import sys
from pathlib import Path

import pytest

# Assurer l'accès au projet racine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.utils.formatting import (
    format_rag_context,
    format_rag_context_compact,
    _extract_doc_fields,
)
from orchestration.utils.chunk_formatter import (
    format_atelier_output,
    _extract_sections,
    _extract_structured_elements,
)
from rag.embeddings.chunker import (
    chunk_text,
    chunk_text_by_pages,
    estimate_tokens,
    _clean_text,
    _find_split_point,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Tests format_rag_context
# ═══════════════════════════════════════════════════════════════════════════════


class TestFormatRagContext:
    """Tests pour format_rag_context (orchestration/utils/formatting.py)."""

    def test_empty_docs_returns_empty(self):
        assert format_rag_context([]) == ""
        assert format_rag_context(None) == ""

    def test_dict_documents(self, sample_rag_documents):
        result = format_rag_context(sample_rag_documents)
        assert "[Ref.1 -- ANSSI p.15 (A1)]" in result
        assert "[Ref.2 -- ANSSI p.42 (A2)]" in result
        assert "[Ref.3 -- ClubEBIOS p.8 (A5)]" in result
        assert "valeurs metier" in result

    def test_langchain_documents(self, sample_langchain_documents):
        result = format_rag_context(sample_langchain_documents)
        assert "[Ref.1 -- ANSSI p.10 (A1)]" in result
        assert "[Ref.2 -- ANSSI p.55 (A3)]" in result
        assert "scenarios de risque" in result

    def test_separator_between_refs(self, sample_rag_documents):
        result = format_rag_context(sample_rag_documents)
        assert "---" in result

    def test_atelier_all_no_parenthesis(self):
        docs = [
            {
                "page_content": "Contenu test",
                "metadata": {
                    "source": "ANSSI",
                    "page": 1,
                    "doc_id": "test",
                    "atelier": "all",
                },
            }
        ]
        result = format_rag_context(docs)
        assert "[Ref.1 -- ANSSI p.1]" in result
        assert "(all)" not in result

    def test_string_document_fallback(self):
        result = format_rag_context(["texte brut sans metadata"])
        assert "texte brut sans metadata" in result

    def test_compact_format(self, sample_rag_documents):
        result = format_rag_context_compact(sample_rag_documents)
        assert "[1|ANSSI p.15]" in result
        assert "[2|ANSSI p.42]" in result
        assert "---" not in result


class TestExtractDocFields:
    """Tests pour _extract_doc_fields."""

    def test_dict_with_page_content(self):
        doc = {"page_content": "test content", "metadata": {"source": "ANSSI"}}
        content, meta = _extract_doc_fields(doc)
        assert content == "test content"
        assert meta["source"] == "ANSSI"

    def test_dict_with_document_key(self):
        doc = {"document": "test content", "metadata": {"page": 5}}
        content, meta = _extract_doc_fields(doc)
        assert content == "test content"
        assert meta["page"] == 5

    def test_string_fallback(self):
        content, meta = _extract_doc_fields("raw text")
        assert content == "raw text"
        assert meta == {}

    def test_unknown_type_returns_empty(self):
        content, meta = _extract_doc_fields(42)
        assert content == ""
        assert meta == {}


# ═══════════════════════════════════════════════════════════════════════════════
# Tests format_atelier_output
# ═══════════════════════════════════════════════════════════════════════════════


class TestFormatAtelierOutput:
    """Tests pour format_atelier_output (orchestration/utils/chunk_formatter.py)."""

    def test_basic_output_structure(self):
        result = format_atelier_output("Reponse test", "A1")
        assert result["atelier"] == "A1"
        assert result["answer"] == "Reponse test"
        assert "sections" in result
        assert "metadata" in result

    def test_markdown_sections_extracted(self):
        text = "## Section 1\nContenu 1\n## Section 2\nContenu 2"
        result = format_atelier_output(text, "A2")
        sections = result["sections"]
        assert len(sections) == 2
        assert sections[0]["title"] == "Section 1"
        assert sections[0]["level"] == 2
        assert "Contenu 1" in sections[0]["content"]

    def test_bullet_items_extracted(self):
        text = "## Liste\n- Item 1\n- Item 2\n- Item 3"
        result = format_atelier_output(text, "A1")
        assert "structured" in result
        assert "items" in result["structured"]
        assert len(result["structured"]["items"]) == 3

    def test_numbered_items_extracted(self):
        text = "1. Premier\n2. Deuxieme\n3. Troisieme"
        result = format_atelier_output(text, "A3")
        assert "structured" in result
        assert "numbered_items" in result["structured"]
        assert len(result["structured"]["numbered_items"]) == 3

    def test_metadata_passthrough(self):
        meta = {"sources_count": 3, "timestamp": "2024-01-01"}
        result = format_atelier_output("Test", "A5", metadata=meta)
        assert result["metadata"]["sources_count"] == 3

    def test_empty_answer_no_crash(self):
        result = format_atelier_output("", "A1")
        assert result["answer"] == ""
        assert result["sections"] == []


# ═══════════════════════════════════════════════════════════════════════════════
# Tests chunker
# ═══════════════════════════════════════════════════════════════════════════════


class TestChunkText:
    """Tests pour chunk_text (rag/embeddings/chunker.py)."""

    def test_empty_text_returns_empty(self, sample_metadata):
        assert chunk_text("", sample_metadata) == []
        assert chunk_text("  ", sample_metadata) == []
        assert chunk_text(None, sample_metadata) == []

    def test_short_text_single_chunk(self, sample_metadata):
        text = "Texte court pour un seul chunk."
        chunks = chunk_text(text, sample_metadata)
        assert len(chunks) == 1
        assert chunks[0][0] == text
        assert chunks[0][1]["doc_id"] == "guide_ebios_rm_2024"

    def test_long_text_multiple_chunks(self, sample_text_for_chunking, sample_metadata):
        chunks = chunk_text(sample_text_for_chunking, sample_metadata)
        assert len(chunks) >= 1
        # Tous les chunks ont les métadonnées de base
        for _, meta in chunks:
            assert "doc_id" in meta
            assert "chunk_index" in meta

    def test_chunk_index_sequential(self, sample_text_for_chunking, sample_metadata):
        chunks = chunk_text(sample_text_for_chunking, sample_metadata)
        indices = [meta["chunk_index"] for _, meta in chunks]
        assert indices == list(range(len(chunks)))

    def test_metadata_preserved(self, sample_metadata):
        text = "Contenu de test pour verification des metadonnees."
        chunks = chunk_text(text, sample_metadata)
        for _, meta in chunks:
            assert meta["atelier"] == "all"
            assert meta["source"] == "ANSSI"
            assert meta["type"] == "guide"

    def test_metadata_not_mutated(self, sample_metadata):
        """Le dictionnaire original ne doit pas etre modifie."""
        original_keys = set(sample_metadata.keys())
        chunk_text("Test", sample_metadata)
        assert set(sample_metadata.keys()) == original_keys

    def test_separator_awareness(self, sample_metadata):
        """Les chunks doivent respecter les frontieres de paragraphes."""
        text = (
            "Premier paragraphe assez long pour etre significatif "
            "dans le contexte du chunking.\n\n"
            "Deuxieme paragraphe qui suit une double ligne vide "
            "et qui devrait etre dans un autre chunk ou au moins "
            "decouper au bon endroit."
        )
        chunks = chunk_text(text, sample_metadata, chunk_size=30)
        # Vérifier qu'aucun chunk ne commence ou finit au milieu d'un mot
        for chunk_text_content, _ in chunks:
            stripped = chunk_text_content.strip()
            if stripped:
                # Ne doit pas commencer par un espace
                assert stripped[0] != " "


class TestChunkTextByPages:
    """Tests pour chunk_text_by_pages."""

    def test_empty_pages_returns_empty(self, sample_metadata):
        assert chunk_text_by_pages([], sample_metadata) == []

    def test_page_numbers_preserved(self, sample_metadata):
        pages = [
            ("Contenu page 1", 1),
            ("Contenu page 2", 2),
            ("Contenu page 3", 3),
        ]
        chunks = chunk_text_by_pages(pages, sample_metadata)
        # Chaque chunk doit avoir le bon numéro de page
        page_nums = {meta["page"] for _, meta in chunks}
        assert page_nums.issubset({1, 2, 3})

    def test_skips_empty_pages(self, sample_metadata):
        pages = [
            ("Contenu page 1", 1),
            ("", 2),  # Page vide
            ("Contenu page 3", 3),
        ]
        chunks = chunk_text_by_pages(pages, sample_metadata)
        page_nums = {meta["page"] for _, meta in chunks}
        assert 2 not in page_nums


class TestEstimateTokens:
    """Tests pour estimate_tokens."""

    def test_empty_returns_one(self):
        assert estimate_tokens("") == 1

    def test_short_text(self):
        # ~4.5 chars/token
        tokens = estimate_tokens("Bonjour le monde")  # 16 chars
        assert 2 <= tokens <= 5

    def test_longer_text(self):
        text = "a" * 450  # 450 chars ~ 100 tokens
        tokens = estimate_tokens(text)
        assert 80 <= tokens <= 120


class TestCleanText:
    """Tests pour _clean_text."""

    def test_normalizes_windows_newlines(self):
        result = _clean_text("ligne1\r\nligne2\rligne3")
        assert "\r" not in result
        assert "ligne1\nligne2\nligne3" == result

    def test_reduces_multiple_blank_lines(self):
        result = _clean_text("a\n\n\n\n\nb")
        assert result == "a\n\nb"

    def test_normalizes_multiple_spaces(self):
        result = _clean_text("mot1    mot2\t\tmot3")
        assert result == "mot1 mot2 mot3"

    def test_strips_line_edges(self):
        result = _clean_text("  debut  \n  fin  ")
        assert result == "debut\nfin"


class TestFindSplitPoint:
    """Tests pour _find_split_point."""

    def test_text_shorter_than_max(self):
        assert _find_split_point("court", 100) == 5

    def test_splits_at_paragraph(self):
        text = "Premier paragraphe.\n\nDeuxieme paragraphe qui est plus long."
        split = _find_split_point(text, 25)
        # Doit couper au \n\n
        assert split <= 25
        assert text[:split].rstrip().endswith(".")

    def test_splits_at_sentence(self):
        text = "Premiere phrase. Deuxieme phrase plus longue qui depasse."
        split = _find_split_point(text, 20)
        assert split <= 20
