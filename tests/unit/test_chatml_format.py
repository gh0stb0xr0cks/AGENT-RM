"""
tests/unit/test_chatml_format.py — Tests du format ChatML produit par 05_format_chatml.py.

Conforme à AGENTS.md §5.4. Aucun appel LLM ni réseau requis.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "corpus" / "scripts"))
from schema import SYSTEM_PROMPT, CorpusExample, Message

_spec = importlib.util.spec_from_file_location(
    "chatml_mod",
    Path(__file__).resolve().parents[2]
    / "corpus" / "scripts" / "05_format_chatml.py",
)
_chatml = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_chatml)

to_chatml_text = _chatml.to_chatml_text


def _make_example(is_ce: bool = False) -> CorpusExample:
    return CorpusExample(
        id="a3_sante_0001",
        atelier="A3",
        secteur="sante",
        source="counterexample" if is_ce else "synthetic",
        is_counterexample=is_ce,
        error_type="forbidden_term" if is_ce else None,
        messages=[
            Message(role="user",      content="Question de test ?"),
            Message(role="assistant", content="Réponse de test avec G3 et V2."),
        ],
    )


def test_chatml_contains_system_prompt():
    text = to_chatml_text(_make_example())
    assert SYSTEM_PROMPT[:50] in text, "System prompt must appear in ChatML output"


def test_chatml_starts_with_im_start_system():
    text = to_chatml_text(_make_example())
    assert text.startswith("<|im_start|>system\n"), (
        f"ChatML must start with '<|im_start|>system\\n', got: {text[:40]!r}"
    )


def test_chatml_ends_with_im_end():
    text = to_chatml_text(_make_example())
    assert text.endswith("<|im_end|>"), (
        f"ChatML must end with '<|im_end|>', got last 20 chars: {text[-20:]!r}"
    )


def test_chatml_has_three_turns():
    text = to_chatml_text(_make_example())
    count = text.count("<|im_start|>")
    assert count == 3, (
        f"ChatML must have exactly 3 turns (system/user/assistant), got {count}"
    )


def test_counterexample_excluded_by_default():
    result = to_chatml_text(_make_example(is_ce=True))
    assert result is None, (
        "Counter-examples must be excluded by default (to_chatml_text returns None)"
    )


def test_counterexample_included_with_flag():
    result = to_chatml_text(_make_example(is_ce=True), include_counterexamples=True)
    assert result is not None, (
        "Counter-examples must be included when include_counterexamples=True"
    )
    assert result.count("<|im_start|>") == 3
