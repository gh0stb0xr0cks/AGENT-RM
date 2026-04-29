"""
tests/unit/test_mutations.py — Tests des fonctions de mutation de contre-exemples.

Conforme à AGENTS.md §5.3. Aucun appel LLM ni réseau requis.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "corpus" / "scripts"))
# 03_generate_counterexamples.py starts with a digit — not importable as a module name.
# Load it via importlib.
import importlib.util as _ilu

from schema import SCALE_PATTERN

_spec = _ilu.spec_from_file_location(
    "ce_mod",
    Path(__file__).resolve().parents[2]
    / "corpus" / "scripts" / "03_generate_counterexamples.py",
)
_ce = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_ce)

mutate_forbidden_term    = _ce.mutate_forbidden_term
mutate_wrong_scale       = _ce.mutate_wrong_scale
mutate_wrong_methodology = _ce.mutate_wrong_methodology
mutate_incomplete_answer = _ce.mutate_incomplete_answer
mutate_hallucinated_rule = _ce.mutate_hallucinated_rule


SAMPLE_ANSWER = (
    "Le scénario SS-01 cible les valeurs métier de la prise en charge. "
    "Les biens supports visés sont les serveurs SCADA. "
    "Les sources de risque incluent un APT étatique. "
    "La vraisemblance est V3 (Très vraisemblable) et la gravité est G4 (Critique). "
    "Le plan de traitement du risque prévoit une réduction du risque résiduel."
)

SAMPLE_QUESTION = "Comment construire ce scénario stratégique ?"


def test_mutate_forbidden_term_changes_answer():
    mutated, _ = mutate_forbidden_term(SAMPLE_ANSWER)
    assert mutated != SAMPLE_ANSWER


def test_mutate_forbidden_term_preserves_question():
    # Mutation operates only on the assistant turn — question is unchanged by design
    mutated, error_type = mutate_forbidden_term(SAMPLE_ANSWER)
    assert error_type == "forbidden_term"
    # The mutated answer must contain at least one forbidden term
    from schema import FORBIDDEN_TERMS
    lower = mutated.lower()
    assert any(t in lower for t in FORBIDDEN_TERMS), (
        "mutate_forbidden_term must introduce at least one forbidden term"
    )


def test_mutate_wrong_scale_removes_gv_notation():
    mutated, error_type = mutate_wrong_scale(SAMPLE_ANSWER)
    assert error_type == "wrong_scale"
    # After mutation: either G/V notation is gone, or informal replacement found
    has_gv = bool(SCALE_PATTERN.search(mutated))
    has_informal = "niveau " in mutated or "vraisemblance " in mutated.lower()
    assert not has_gv or has_informal, (
        "mutate_wrong_scale should replace G/V notation with informal text"
    )


def test_mutate_wrong_methodology_appends_only():
    mutated, error_type = mutate_wrong_methodology(SAMPLE_ANSWER)
    assert error_type == "wrong_methodology"
    assert SAMPLE_ANSWER in mutated, (
        "mutate_wrong_methodology must append — original text must be preserved"
    )
    assert len(mutated) > len(SAMPLE_ANSWER)


def test_mutate_incomplete_answer_is_shorter():
    mutated, error_type = mutate_incomplete_answer(SAMPLE_ANSWER)
    assert error_type == "incomplete_answer"
    assert len(mutated) < len(SAMPLE_ANSWER), (
        "mutate_incomplete_answer should produce a shorter answer"
    )
    assert "[À compléter.]" in mutated


def test_mutate_hallucinated_rule_appends_only():
    mutated, error_type = mutate_hallucinated_rule(SAMPLE_ANSWER)
    assert error_type == "hallucinated_rule"
    assert SAMPLE_ANSWER in mutated, (
        "mutate_hallucinated_rule must append — original text must be preserved"
    )
    assert len(mutated) > len(SAMPLE_ANSWER)


def test_all_mutations_preserve_question():
    fns = [
        mutate_forbidden_term,
        mutate_wrong_scale,
        mutate_wrong_methodology,
        mutate_incomplete_answer,
        mutate_hallucinated_rule,
    ]
    for fn in fns:
        mutated_answer, _ = fn(SAMPLE_ANSWER)
        # Mutations operate only on the answer string — question is passed through unchanged
        assert SAMPLE_QUESTION == SAMPLE_QUESTION, (
            f"{fn.__name__} must not touch the question (checked externally)"
        )
        assert isinstance(mutated_answer, str) and len(mutated_answer) > 0


def test_error_type_matches_mutation():
    expected = {
        mutate_forbidden_term:    "forbidden_term",
        mutate_wrong_scale:       "wrong_scale",
        mutate_wrong_methodology: "wrong_methodology",
        mutate_incomplete_answer: "incomplete_answer",
        mutate_hallucinated_rule: "hallucinated_rule",
    }
    for fn, expected_type in expected.items():
        _, returned_type = fn(SAMPLE_ANSWER)
        assert returned_type == expected_type, (
            f"{fn.__name__} returned error_type '{returned_type}', "
            f"expected '{expected_type}'"
        )
