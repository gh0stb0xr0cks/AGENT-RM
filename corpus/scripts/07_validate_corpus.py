"""
07_validate_corpus.py — Validation finale du corpus avant lancement du fine-tuning.

Neuf vérifications (AGENTS.md §4.7) :
  1. Existence des fichiers            — train/eval/test non vides
  2. Comptes minimum                   — train ≥ 7 000 · eval ≥ 800 · test ≥ 800
  3. Couverture des 70 strates         — chaque (atelier × secteur) dans chaque split
  4. Zéro terme interdit               — dans les exemples V1 + V2 des trois splits
  5. Présence de cotation G/V          — 100 % des exemples A3/A4/A5 V1+V2
  6. Taux de contre-exemples           — V3 ≤ 20 % du train
  7. Régression metadata               — clés requises §3.3 présentes (sur filtered.jsonl)
  8. Unicité des IDs                   — pas de doublon sur train+eval+test combinés
  9. Absence de fuite                  — aucun ID commun entre les splits

Exit 0 = PASS · Exit 1 = FAIL (ou tout avertissement en mode --strict).

Produit : corpus/processed/validation_report.json

Usage :
  python 07_validate_corpus.py
  python 07_validate_corpus.py --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import (
    ATELIERS,
    FORBIDDEN_TERMS,
    SCALE_PATTERN,
    SECTORS,
)

ROOT         = Path(__file__).resolve().parents[1]
DATASETS_DIR = ROOT / "datasets"
PROCESSED_DIR = ROOT / "processed"
REPORT_PATH  = PROCESSED_DIR / "validation_report.json"
FILTERED_PATH = PROCESSED_DIR / "filtered.jsonl"

MIN_COUNTS = {"train": 7_000, "eval": 800, "test": 800}

EXPECTED_STRATA: set[str] = {f"{a}_{s}" for a in ATELIERS for s in SECTORS}

# Required metadata keys per source type (AGENTS.md §3.3)
REQUIRED_METADATA: dict[str, set[str]] = {
    "anssi_doc":     {"source_chunk", "source_document", "word_count", "has_gv_scale"},
    "synthetic":     {"source_chunk", "generation_theme", "generation_backend",
                      "generation_model", "word_count", "has_gv_scale"},
    "counterexample": {"source_chunk", "parent_id", "mutation_strategy",
                       "word_count", "has_gv_scale"},
}

CHATML_RE = re.compile(
    r'<\|im_start\|>system\n.+?<\|im_end\|>\n'
    r'<\|im_start\|>user\n.+?<\|im_end\|>\n'
    r'<\|im_start\|>assistant\n.+?<\|im_end\|>',
    re.DOTALL,
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def iter_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


def load_split(path: Path) -> list[dict]:
    return list(iter_jsonl(path))


# ─────────────────────────────────────────────────────────────────────────────
# Check functions — each returns (passed: bool, messages: list[str])
# ─────────────────────────────────────────────────────────────────────────────

def check_file_existence(splits: dict[str, Path]) -> tuple[bool, list[str]]:
    """Check 1 : tous les fichiers existent et sont non vides."""
    errors: list[str] = []
    for name, path in splits.items():
        if not path.exists():
            errors.append(f"{name}.jsonl absent : {path}")
        elif path.stat().st_size == 0:
            errors.append(f"{name}.jsonl vide")
    return len(errors) == 0, errors


def check_min_counts(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 2 : comptes minimaux (AGENTS.md §4.7)."""
    errors: list[str] = []
    for name, minimum in MIN_COUNTS.items():
        n = len(loaded.get(name, []))
        if n < minimum:
            errors.append(f"{name}.jsonl : {n} exemples < minimum requis {minimum}")
    return len(errors) == 0, errors


def check_stratum_coverage(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 3 : les 70 strates (atelier × secteur) présentes dans chaque split."""
    errors: list[str] = []
    for name, records in loaded.items():
        present = {f"{r.get('atelier','?')}_{r.get('secteur','?')}" for r in records}
        missing = sorted(EXPECTED_STRATA - present)
        if missing:
            errors.append(
                f"{name}.jsonl : {len(missing)} strate(s) manquante(s) : "
                f"{', '.join(missing[:10])}"
                + (" ..." if len(missing) > 10 else "")
            )
    return len(errors) == 0, errors


_ASSISTANT_RE = re.compile(
    r'<\|im_start\|>assistant\n(.*?)<\|im_end\|>', re.DOTALL
)
_USER_RE = re.compile(
    r'<\|im_start\|>user\n(.*?)<\|im_end\|>', re.DOTALL
)


def _extract_ua(text: str) -> str:
    """Extrait uniquement les tours user + assistant (pas le system prompt)."""
    user      = (_USER_RE.search(text) or type("", (), {"group": lambda *_: ""})()).group(1) or ""
    assistant = (_ASSISTANT_RE.search(text) or type("", (), {"group": lambda *_: ""})()).group(1) or ""
    return (user + " " + assistant).strip()


def check_zero_forbidden_terms(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 4 : zéro terme interdit dans les tours user+assistant des V1+V2."""
    errors: list[str] = []
    for name, records in loaded.items():
        for r in records:
            if r.get("is_counterexample"):
                continue
            ua = _extract_ua(r.get("text", "")).lower()
            found = [t for t in FORBIDDEN_TERMS if t in ua]
            if found:
                errors.append(
                    f"{name}.jsonl id={r.get('id','?')} : terme(s) interdit(s) : "
                    f"{', '.join(found[:3])}"
                )
    return len(errors) == 0, errors


def check_gv_scale_presence(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 5 : cotation G/V présente dans 100 % des exemples A3/A4/A5 V1+V2."""
    errors: list[str] = []
    for name, records in loaded.items():
        for r in records:
            if r.get("is_counterexample"):
                continue
            if r.get("atelier") not in ("A3", "A4", "A5"):
                continue
            assistant = _ASSISTANT_RE.search(r.get("text", ""))
            if not assistant or not SCALE_PATTERN.search(assistant.group(1)):
                errors.append(
                    f"{name}.jsonl id={r.get('id','?')} "
                    f"({r.get('atelier')}) : cotation G/V absente dans le tour assistant"
                )
    return len(errors) == 0, errors


def check_counterexample_rate(train: list[dict]) -> tuple[bool, list[str]]:
    """Check 6 : contre-exemples ≤ 20 % du train."""
    n_ce    = sum(1 for r in train if r.get("is_counterexample"))
    n_total = len(train)
    rate    = n_ce / n_total if n_total else 0
    if rate > 0.20:
        return False, [
            f"Taux de contre-exemples dans train : {rate:.1%} > 20 % "
            f"({n_ce}/{n_total})"
        ]
    return True, []


def check_metadata_regression(filtered_path: Path) -> tuple[bool, list[str]]:
    """Check 7 : clés metadata requises §3.3 présentes dans filtered.jsonl."""
    if not filtered_path.exists():
        return True, ["filtered.jsonl absent — vérification metadata ignorée (warning)"]

    errors: list[str] = []
    for d in iter_jsonl(filtered_path):
        source   = d.get("source", "")
        required = REQUIRED_METADATA.get(source)
        if required is None:
            continue  # source inconnue — déjà capturé par 04
        metadata = d.get("metadata", {})
        missing  = required - set(metadata.keys())
        if missing:
            errors.append(
                f"id={d.get('id','?')} source={source} : "
                f"clé(s) metadata manquante(s) : {', '.join(sorted(missing))}"
            )
    return len(errors) == 0, errors


def check_id_uniqueness(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 8 : IDs uniques sur train+eval+test combinés."""
    seen:  dict[str, str] = {}
    errors: list[str] = []
    for name, records in loaded.items():
        for r in records:
            id_ = r.get("id", "")
            if id_ in seen:
                errors.append(
                    f"ID dupliqué '{id_}' dans {name}.jsonl "
                    f"(déjà vu dans {seen[id_]})"
                )
            else:
                seen[id_] = name
    return len(errors) == 0, errors


def check_split_leakage(loaded: dict[str, list[dict]]) -> tuple[bool, list[str]]:
    """Check 9 : aucun ID commun entre les splits."""
    split_ids: dict[str, set[str]] = {
        name: {r.get("id", "") for r in records}
        for name, records in loaded.items()
    }
    errors: list[str] = []
    names = list(split_ids)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            common = split_ids[a] & split_ids[b]
            if common:
                sample = sorted(common)[:5]
                errors.append(
                    f"Fuite {a}↔{b} : {len(common)} ID(s) en commun — "
                    f"ex: {', '.join(sample)}"
                )
    return len(errors) == 0, errors


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validation finale du corpus EBIOS RM (AGENTS.md §4.7)"
    )
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 sur tout avertissement")
    args = parser.parse_args()

    split_paths = {
        "train": DATASETS_DIR / "train.jsonl",
        "eval":  DATASETS_DIR / "eval.jsonl",
        "test":  DATASETS_DIR / "test.jsonl",
    }

    all_errors:   list[str] = []
    all_warnings: list[str] = []
    checks: dict[str, object] = {}

    # ── Check 1 : existence ──────────────────────────────────────────────────
    ok, msgs = check_file_existence(split_paths)
    checks["file_existence"] = ok
    if not ok:
        all_errors.extend(msgs)
        # Cannot continue without the files
        _write_report(checks, all_errors, all_warnings)
        sys.exit(1)

    loaded = {name: load_split(path) for name, path in split_paths.items()}
    print(f"  train : {len(loaded['train'])} exemples")
    print(f"  eval  : {len(loaded['eval'])}  exemples")
    print(f"  test  : {len(loaded['test'])}  exemples")

    # ── Check 2 : comptes minimum ────────────────────────────────────────────
    ok, msgs = check_min_counts(loaded)
    checks["min_counts"] = {
        name: len(loaded.get(name, [])) >= MIN_COUNTS[name]
        for name in MIN_COUNTS
    }
    if not ok:
        all_errors.extend(msgs)

    # ── Check 3 : couverture des 70 strates ─────────────────────────────────
    ok, msgs = check_stratum_coverage(loaded)
    checks["stratum_coverage"] = {
        name: not any(name in m for m in msgs) for name in loaded
    }
    if not ok:
        all_errors.extend(msgs)

    # ── Check 4 : zéro terme interdit ───────────────────────────────────────
    ok, msgs = check_zero_forbidden_terms(loaded)
    checks["zero_forbidden_terms"] = ok
    if not ok:
        all_errors.extend(msgs)

    # ── Check 5 : cotation G/V ───────────────────────────────────────────────
    ok, msgs = check_gv_scale_presence(loaded)
    checks["gv_scale_presence"] = ok
    if not ok:
        all_errors.extend(msgs)

    # ── Check 6 : taux de contre-exemples ───────────────────────────────────
    ok, msgs = check_counterexample_rate(loaded["train"])
    checks["counterexample_rate"] = ok
    if not ok:
        all_errors.extend(msgs)

    # ── Check 7 : régression metadata (sur filtered.jsonl) ──────────────────
    ok, msgs = check_metadata_regression(FILTERED_PATH)
    checks["metadata_regression"] = ok
    if not ok:
        all_errors.extend(msgs)
    elif msgs:  # warnings (ex: filtered.jsonl absent)
        all_warnings.extend(msgs)

    # ── Check 8 : unicité des IDs ────────────────────────────────────────────
    ok, msgs = check_id_uniqueness(loaded)
    checks["id_uniqueness"] = ok
    if not ok:
        all_errors.extend(msgs)

    # ── Check 9 : absence de fuite ───────────────────────────────────────────
    ok, msgs = check_split_leakage(loaded)
    checks["split_leakage"] = ok
    if not ok:
        all_errors.extend(msgs)

    # ── Rapport ──────────────────────────────────────────────────────────────
    _write_report(checks, all_errors, all_warnings)

    # ── Résumé console ───────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    for check_name, result in checks.items():
        symbol = "✓" if (result is True or (isinstance(result, dict) and all(result.values()))) else "✗"
        print(f"  {symbol}  {check_name}")

    if all_errors:
        print(f"\n  {len(all_errors)} erreur(s) bloquante(s) :")
        for e in all_errors[:10]:
            print(f"    - {e}")
        if len(all_errors) > 10:
            print(f"    ... ({len(all_errors) - 10} autres — voir {REPORT_PATH})")

    if all_warnings:
        print(f"\n  {len(all_warnings)} avertissement(s) :")
        for w in all_warnings[:5]:
            print(f"    - {w}")

    print(f"\nRapport → {REPORT_PATH}")

    fail = len(all_errors) > 0 or (args.strict and len(all_warnings) > 0)
    status = "FAIL" if fail else "PASS"
    print(f"Statut : {status}")
    sys.exit(1 if fail else 0)


def _write_report(
    checks: dict[str, object],
    errors: list[str],
    warnings: list[str],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "status":   "FAIL" if errors else "PASS",
        "checks":   checks,
        "errors":   errors,
        "warnings": warnings,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
