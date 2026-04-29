"""
tests/integration/test_pipeline.py — Test du pipeline corpus en micro-corpus.

Conforme à AGENTS.md §5.5.
Fixture : 3 exemples valides par strate (atelier × secteur) = 210 exemples.
Aucun appel LLM ni réseau requis — les exemples sont écrits depuis fixtures.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT   = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "corpus" / "scripts"

sys.path.insert(0, str(SCRIPTS_DIR))
from schema import ATELIERS, SECTORS, SYSTEM_PROMPT, CorpusExample, Message  # noqa: E402

# ─────────────────────────────────────────────────────────────────────────────
# Helpers to load scripts via importlib (filenames start with digits)
# ─────────────────────────────────────────────────────────────────────────────

def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_qf     = _load("qf",     "04_quality_filter.py")
_chatml = _load("chatml", "05_format_chatml.py")
_split  = _load("split",  "06_stratified_split.py")
_val    = _load("val",    "07_validate_corpus.py")


# ─────────────────────────────────────────────────────────────────────────────
# Fixture — micro-corpus : 3 valid CorpusExamples per (atelier × sector)
# ─────────────────────────────────────────────────────────────────────────────

def _valid_answer(atelier: str) -> str:
    base = (
        "Les valeurs métier identifiées sont essentielles pour l'organisation. "
        "Les biens supports comprennent les serveurs et les réseaux internes. "
        "Les sources de risque incluent des groupes APT et des cybercriminels. "
        "Le plan de traitement du risque prévoit des mesures de réduction. "
    ) * 5
    if atelier in ("A3", "A4", "A5"):
        base += " La vraisemblance est V3 (Très vraisemblable). La gravité est G4 (Critique)."
    return base


def _make_example(atelier: str, secteur: str, idx: int) -> dict:
    return CorpusExample(
        id=f"{atelier.lower()}_{secteur}_{idx:04d}",
        atelier=atelier,
        secteur=secteur,
        source="synthetic",
        messages=[
            Message(role="user",      content=f"Comment appliquer {atelier} dans le secteur {secteur} — exemple {idx} ?"),
            Message(role="assistant", content=_valid_answer(atelier)),
        ],
        metadata={
            "source_chunk":       None,
            "generation_theme":   f"{atelier}_t00",
            "generation_backend": "test",
            "generation_model":   "fixture",
            "word_count":         len(_valid_answer(atelier).split()),
            "has_gv_scale":       atelier in ("A3", "A4", "A5"),
        },
    ).to_dict()


@pytest.fixture(scope="module")
def micro_corpus(tmp_path_factory):
    """
    Écrit 210 exemples valides (3 par strate) dans tmp_path/raw/synthetics/.
    Retourne tmp_path.
    """
    base = tmp_path_factory.mktemp("corpus")
    synth_dir = base / "raw" / "synthetics"
    synth_dir.mkdir(parents=True)
    (base / "processed").mkdir()
    (base / "datasets").mkdir()

    for atelier in ATELIERS:
        for secteur in SECTORS:
            shard = synth_dir / f"{atelier.lower()}_{secteur}.jsonl"
            with open(shard, "w", encoding="utf-8") as f:
                for i in range(3):
                    rec = _make_example(atelier, secteur, i)
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return base


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

def test_filter_accepts_all_valid_examples(micro_corpus):
    """Gate 04 : les 210 exemples valides doivent tous passer."""
    synth_dir    = micro_corpus / "raw" / "synthetics"
    filtered_out = micro_corpus / "processed" / "filtered.jsonl"

    seen:     set[str]  = set()
    accepted: list[dict] = []

    for path in sorted(synth_dir.glob("*.jsonl")):
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                ok, reasons = _qf.filter_example(d, min_words=80, max_words=2000, seen_hashes=seen)
                assert ok, f"Valid example rejected in {path.name}: {reasons}"
                accepted.append(d)

    assert len(accepted) == 210, f"Expected 210 accepted, got {len(accepted)}"

    with open(filtered_out, "w", encoding="utf-8") as f:
        for d in sorted(accepted, key=lambda r: (r["atelier"], r["secteur"], r["id"])):
            f.write(json.dumps(d, ensure_ascii=False) + "\n")


def test_split_covers_all_strata(micro_corpus):
    """Gate 06 : toutes les 70 strates présentes dans chaque split (3 ex/strate)."""
    filtered_out  = micro_corpus / "processed" / "filtered.jsonl"
    chatml_out    = micro_corpus / "datasets"  / "filtered_chatml.jsonl"

    if not filtered_out.exists():
        pytest.skip("Run test_filter_accepts_all_valid_examples first")

    # Format ChatML
    records_chatml = []
    with open(filtered_out, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d  = json.loads(line)
            ex = CorpusExample.from_dict(d)
            text = _chatml.to_chatml_text(ex)
            if text:
                records_chatml.append({
                    "text": text, "id": ex.id, "atelier": ex.atelier,
                    "secteur": ex.secteur, "source": ex.source,
                    "is_counterexample": ex.is_counterexample,
                })

    with open(chatml_out, "w", encoding="utf-8") as f:
        for r in records_chatml:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Split (3 examples/strate → all to train because n < 3 guard triggers at n=3)
    train, eval_, test = _split.stratified_split(
        records_chatml, train_ratio=0.34, eval_ratio=0.33, test_ratio=0.33, seed=42
    )

    for name, split in [("train", train), ("eval", eval_), ("test", test)]:
        path = micro_corpus / "datasets" / f"{name}.jsonl"
        with open(path, "w", encoding="utf-8") as f:
            for r in split:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # With only 3 examples/strate and equal ratios, each split gets ≥1 per strate
    expected = {f"{a}_{s}" for a in ATELIERS for s in SECTORS}
    for name, split in [("train", train), ("eval", eval_), ("test", test)]:
        present = {f"{r['atelier']}_{r['secteur']}" for r in split}
        missing = expected - present
        assert not missing, f"{name} missing strata: {sorted(missing)[:5]}"


def test_validate_passes_on_clean_corpus(micro_corpus):
    """Gate 07 checks 3-9 pass on our clean micro-corpus (min-count check will warn)."""
    train_path = micro_corpus / "datasets" / "train.jsonl"
    eval_path  = micro_corpus / "datasets" / "eval.jsonl"
    test_path  = micro_corpus / "datasets" / "test.jsonl"

    if not train_path.exists():
        pytest.skip("Run test_split_covers_all_strata first")

    loaded = {
        "train": list(_val.iter_jsonl(train_path)),
        "eval":  list(_val.iter_jsonl(eval_path)),
        "test":  list(_val.iter_jsonl(test_path)),
    }

    # Checks that should PASS on clean data
    ok, msgs = _val.check_zero_forbidden_terms(loaded)
    assert ok, f"Forbidden terms found in clean corpus: {msgs[:3]}"

    ok, msgs = _val.check_gv_scale_presence(loaded)
    assert ok, f"Missing G/V scale in clean corpus: {msgs[:3]}"

    ok, msgs = _val.check_id_uniqueness(loaded)
    assert ok, f"Duplicate IDs in clean corpus: {msgs[:3]}"

    ok, msgs = _val.check_split_leakage(loaded)
    assert ok, f"Split leakage in clean corpus: {msgs[:3]}"


def test_validate_fails_on_forbidden_term(micro_corpus):
    """Gate 07 check 4 : un exemple avec terme interdit dans le train → échec."""
    bad_text = (
        "<|im_start|>system\n" + SYSTEM_PROMPT + "\n<|im_end|>\n"
        "<|im_start|>user\nQuestion ?\n<|im_end|>\n"
        "<|im_start|>assistant\nLes biens essentiels sont prioritaires.\n<|im_end|>"
    )
    bad_record = {
        "id": "a1_sante_9999", "atelier": "A1", "secteur": "sante",
        "source": "synthetic", "is_counterexample": False, "text": bad_text,
    }
    ok, msgs = _val.check_zero_forbidden_terms({"train": [bad_record]})
    assert not ok, "Should detect 'biens essentiels' as forbidden term"
    assert any("biens essentiels" in m for m in msgs)


def test_validate_fails_below_minimum_count(micro_corpus):
    """Gate 07 check 2 : avec 210 exemples le seuil de 7 000 n'est pas atteint."""
    loaded = {"train": [{}] * 210, "eval": [{}] * 210, "test": [{}] * 210}
    ok, msgs = _val.check_min_counts(loaded)
    assert not ok, "210 examples should fail the 7 000 minimum"
    assert any("7000" in m for m in msgs)
