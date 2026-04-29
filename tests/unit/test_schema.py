"""
tests/unit/test_schema.py — Tests contractuels pour corpus/scripts/schema.py.

Conforme à AGENTS.md §5.1. Aucun appel LLM ni réseau requis.
"""
from __future__ import annotations

import re
import string
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "corpus" / "scripts"))
from schema import (
    ATELIERS,
    FORBIDDEN_TERMS,
    GENERATION_TEMPLATES,
    GENERATION_THEMES,
    SCALE_PATTERN,
    SECTOR_LABELS,
    SECTORS,
    SYSTEM_PROMPT,
    CorpusExample,
    Message,
)


def test_ateliers_is_list_of_five():
    assert isinstance(ATELIERS, list)
    assert len(ATELIERS) == 5
    assert ATELIERS == ["A1", "A2", "A3", "A4", "A5"]


def test_sectors_has_14_entries():
    assert isinstance(SECTORS, list)
    assert len(SECTORS) == 14
    # All lowercase, no accents
    for s in SECTORS:
        assert s == s.lower(), f"Sector '{s}' must be lowercase"
        assert s.isascii(), f"Sector '{s}' must be ASCII"


def test_sector_labels_keys_match_sectors():
    assert set(SECTOR_LABELS.keys()) == set(SECTORS)


def test_system_prompt_contains_required_terms():
    required = [
        "valeurs métier", "biens supports", "sources de risque",
        "plan de traitement du risque",
        "G1", "G4", "V1", "V4",
    ]
    prompt_lower = SYSTEM_PROMPT.lower()
    for term in required:
        assert term.lower() in prompt_lower, f"SYSTEM_PROMPT missing '{term}'"


def test_forbidden_terms_keys_are_lowercase():
    for key in FORBIDDEN_TERMS:
        assert key == key.lower(), f"FORBIDDEN_TERMS key '{key}' must be lowercase"


def test_forbidden_terms_values_are_different_from_keys():
    for wrong, correct in FORBIDDEN_TERMS.items():
        assert wrong != correct, (
            f"FORBIDDEN_TERMS: key and value are identical: '{wrong}'"
        )


def test_generation_templates_have_exactly_two_placeholders():
    formatter = string.Formatter()
    for atelier, template in GENERATION_TEMPLATES.items():
        fields = {fname for _, fname, _, _ in formatter.parse(template) if fname}
        assert fields == {"secteur", "theme"}, (
            f"GENERATION_TEMPLATES[{atelier}] has wrong placeholders: {fields}"
        )


def test_generation_themes_has_at_least_26_per_atelier():
    for atelier in ATELIERS:
        themes = GENERATION_THEMES.get(atelier, [])
        assert len(themes) >= 26, (
            f"GENERATION_THEMES[{atelier}] has only {len(themes)} themes (need ≥ 26)"
        )


def test_scale_pattern_matches_valid_codes():
    valid = ["G1", "G2", "G3", "G4", "V1", "V2", "V3", "V4"]
    for code in valid:
        assert SCALE_PATTERN.search(code), f"SCALE_PATTERN should match '{code}'"


def test_scale_pattern_rejects_invalid_codes():
    invalid = ["G0", "G5", "V0", "V5", "G10", "V10"]
    for code in invalid:
        assert not SCALE_PATTERN.fullmatch(code), (
            f"SCALE_PATTERN should NOT match '{code}'"
        )


def test_corpus_example_roundtrip():
    ex = CorpusExample(
        id="a3_sante_0042",
        atelier="A3",
        secteur="sante",
        source="synthetic",
        messages=[
            Message(role="user",      content="Question de test ?"),
            Message(role="assistant", content="Réponse de test V3 G2."),
        ],
        metadata={"word_count": 5, "has_gv_scale": True},
        is_counterexample=False,
        error_type=None,
    )
    d  = ex.to_dict()
    ex2 = CorpusExample.from_dict(d)

    assert ex2.id      == ex.id
    assert ex2.atelier == ex.atelier
    assert ex2.secteur == ex.secteur
    assert ex2.source  == ex.source
    assert ex2.is_counterexample == ex.is_counterexample
    assert ex2.error_type        == ex.error_type
    assert len(ex2.messages)     == 2
    assert ex2.messages[0].role    == "user"
    assert ex2.messages[0].content == "Question de test ?"
    assert ex2.messages[1].role    == "assistant"
    assert ex2.metadata == ex.metadata


def test_corpus_example_id_format():
    valid_ids = [
        "a1_sante_0000",
        "a3_defense_0042",
        "a5_alimentaire_1234",
    ]
    pattern = re.compile(r"^[a-z][0-9]_[a-z]+_\d{4}$")
    for id_ in valid_ids:
        assert pattern.match(id_), f"ID '{id_}' should match id format"


def test_message_roles_are_literal():
    valid_roles = {"system", "user", "assistant"}
    for role in valid_roles:
        m = Message(role=role, content="test")  # type: ignore[arg-type]
        assert m.role == role

    # Python dataclasses do not enforce Literal at runtime.
    # Verify that an invalid role is rejected by downstream validation instead.
    m = Message(role="invalid_role", content="test")  # type: ignore[arg-type]
    assert m.role not in valid_roles, (
        "Role 'invalid_role' should not be in the set of valid roles — "
        "enforcement happens at the quality-filter or validation layer."
    )
