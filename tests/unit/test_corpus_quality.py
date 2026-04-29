"""
tests/unit/test_corpus_quality.py — Tests des portes de filtrage de 04_quality_filter.py.

Conforme à AGENTS.md §5.2. Aucun appel LLM ni réseau requis.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "corpus" / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "qf_mod",
    Path(__file__).resolve().parents[2]
    / "corpus" / "scripts" / "04_quality_filter.py",
)
_qf = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_qf)

check_word_count       = _qf.check_word_count
check_forbidden_terms  = _qf.check_forbidden_terms
check_required_terms   = _qf.check_required_terms
check_gv_scale         = _qf.check_gv_scale
check_duplicate        = _qf.check_duplicate
check_structure        = _qf.check_structure
check_secteur          = _qf.check_secteur
check_source_chunk     = _qf.check_source_chunk
filter_example         = _qf.filter_example


def _make_raw(atelier="A3", secteur="sante", source="synthetic",
              question="Comment ?", answer="Réponse.", is_ce=False, error_type=None,
              metadata=None):
    d = {
        "id":      f"{atelier.lower()}_{secteur}_0001",
        "atelier": atelier,
        "secteur": secteur,
        "source":  source,
        "is_counterexample": is_ce,
        "messages": [
            {"role": "user",      "content": question},
            {"role": "assistant", "content": answer},
        ],
        "metadata": metadata or {},
    }
    if is_ce:
        d["error_type"] = error_type or "forbidden_term"
    return d


LONG_ANSWER = "Les valeurs métier sont importantes. " * 30  # ~180 words


def test_reject_forbidden_term_in_assistant_turn():
    issues = check_forbidden_terms("Les biens essentiels sont critiques.")
    assert any("biens essentiels" in i for i in issues)


def test_accept_correct_term_in_assistant_turn():
    issues = check_forbidden_terms("Les valeurs métier sont identifiées.")
    assert issues == []


def test_reject_too_short_answer():
    issues = check_word_count("trop court", min_words=80, max_words=2000)
    assert any("min_word_count" in i for i in issues)


def test_reject_too_long_answer():
    issues = check_word_count("mot " * 2001, min_words=80, max_words=2000)
    assert any("max_word_count" in i for i in issues)


def test_reject_missing_gv_scale_in_a3():
    issues = check_gv_scale("Pas de cotation ici.", "A3")
    assert issues == ["gv_scale_missing"]


def test_accept_gv_scale_in_a3():
    issues = check_gv_scale("La gravité est G3 et la vraisemblance V2.", "A3")
    assert issues == []


def test_accept_missing_gv_scale_in_a1():
    issues = check_gv_scale("Pas de cotation G/V requise pour A1.", "A1")
    assert issues == []


def test_reject_duplicate_question():
    seen: set[str] = set()
    q = "Question identique ?"
    assert check_duplicate(q, seen) == []
    assert check_duplicate(q, seen) == ["duplicate"]


def test_counterexample_skips_forbidden_term_gate():
    seen: set[str] = set()
    d = _make_raw(
        secteur="sante", is_ce=True,
        answer="Les biens essentiels sont prioritaires.",
    )
    ok, reasons = filter_example(d, min_words=1, max_words=9999, seen_hashes=seen)
    assert ok, f"Counter-example should pass despite forbidden term: {reasons}"


def test_reject_invalid_secteur():
    issues = check_secteur("secteur_inconnu")
    assert issues != []


def test_reject_missing_source_chunk_for_volet1():
    seen: set[str] = set()
    d = _make_raw(
        atelier="A1", secteur="sante", source="anssi_doc",
        question="Q ?", answer=LONG_ANSWER,
        metadata={"source_chunk": None},
    )
    ok, reasons = filter_example(d, min_words=80, max_words=2000, seen_hashes=seen)
    assert not ok
    assert any("source_chunk" in r for r in reasons)
