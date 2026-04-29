"""
06_stratified_split.py — Découpage stratifié du corpus en train / eval / test.

Entrée  : corpus/datasets/filtered_chatml.jsonl  (produit par 05_format_chatml.py)

Stratification sur (atelier × secteur) pour garantir la couverture des 70 strates
dans chaque split (AGENTS.md §4.6).

  Train : 80%  (défaut)
  Eval  : 10%
  Test  : 10%

Algorithme par strate (atelier, secteur) :
  1. Shuffle (RNG seeded)
  2. n_test  = max(1, floor(n × test_ratio))
  3. n_eval  = max(1, floor(n × eval_ratio))
  4. n_train = n - n_test - n_eval
  5. Si n < 3 : tout en train (warning)
  Shuffle final de chaque split global.

Invariant : toutes les 70 strates doivent être présentes dans chaque split.
Si l'une manque, le seed est incrémenté et on réessaie (max 20 tentatives).

Produit :
  corpus/datasets/train.jsonl
  corpus/datasets/eval.jsonl
  corpus/datasets/test.jsonl
  corpus/datasets/split_stats.json

Usage :
  python 06_stratified_split.py
  python 06_stratified_split.py --train 0.8 --eval 0.1 --test 0.1 --seed 42
"""
from __future__ import annotations

import argparse
import json
import logging
import math
import random
import sys
from collections import defaultdict
from pathlib import Path

log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from schema import ATELIERS, SECTORS  # noqa: E402

ROOT         = Path(__file__).resolve().parents[1]
CHATML_FILE  = ROOT / "datasets" / "filtered_chatml.jsonl"
DATASETS_DIR = ROOT / "datasets"

EXPECTED_STRATA: set[str] = {
    f"{a}_{s}" for a in ATELIERS for s in SECTORS
}  # 70 strates


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def write_jsonl(records: list[dict], path: Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def strata_present(records: list[dict]) -> set[str]:
    return {f"{r.get('atelier','?')}_{r.get('secteur','?')}" for r in records}


def stratified_split(
    records: list[dict],
    train_ratio: float,
    eval_ratio: float,
    test_ratio: float,
    seed: int,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Split stratifié par (atelier × secteur).
    Retourne (train, eval, test).
    """
    strata: dict[str, list[dict]] = defaultdict(list)
    for r in records:
        key = f"{r.get('atelier','?')}_{r.get('secteur','?')}"
        strata[key].append(r)

    rng = random.Random(seed)
    train, eval_, test = [], [], []

    for key, group in strata.items():
        rng.shuffle(group)
        n = len(group)

        if n < 3:
            log.warning("Strate %s : seulement %d exemple(s) — tout mis en train", key, n)
            train.extend(group)
            continue

        n_test  = max(1, math.floor(n * test_ratio))
        n_eval  = max(1, math.floor(n * eval_ratio))
        n_train = n - n_test - n_eval

        train.extend(group[:n_train])
        eval_.extend(group[n_train:n_train + n_eval])
        test.extend(group[n_train + n_eval:])

    rng.shuffle(train)
    rng.shuffle(eval_)
    rng.shuffle(test)

    return train, eval_, test


def build_stats(
    records: list[dict],
    train: list[dict],
    eval_: list[dict],
    test: list[dict],
    seed: int,
    train_ratio: float,
    eval_ratio: float,
    test_ratio: float,
) -> dict:
    """Produit split_stats.json au format AGENTS.md §4.6."""
    def _by_atelier(lst: list[dict]) -> dict[str, int]:
        d: dict[str, int] = defaultdict(int)
        for r in lst:
            d[r.get("atelier", "?")] += 1
        return dict(sorted(d.items()))

    # 70-entry by_stratum
    by_stratum: dict[str, dict] = {}
    strata_train: dict[str, int] = defaultdict(int)
    strata_eval:  dict[str, int] = defaultdict(int)
    strata_test:  dict[str, int] = defaultdict(int)
    for r in train:
        strata_train[f"{r.get('atelier','?')}_{r.get('secteur','?')}"] += 1
    for r in eval_:
        strata_eval[f"{r.get('atelier','?')}_{r.get('secteur','?')}"]  += 1
    for r in test:
        strata_test[f"{r.get('atelier','?')}_{r.get('secteur','?')}"]  += 1

    for key in sorted(EXPECTED_STRATA):
        by_stratum[key] = {
            "train": strata_train.get(key, 0),
            "eval":  strata_eval.get(key, 0),
            "test":  strata_test.get(key, 0),
        }

    return {
        "seed":   seed,
        "ratios": {"train": train_ratio, "eval": eval_ratio, "test": test_ratio},
        "totals": {
            "train": len(train),
            "eval":  len(eval_),
            "test":  len(test),
        },
        "by_atelier": {
            "train": _by_atelier(train),
            "eval":  _by_atelier(eval_),
            "test":  _by_atelier(test),
        },
        "by_stratum": by_stratum,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Split stratifié du corpus EBIOS RM (AGENTS.md §4.6)"
    )
    parser.add_argument("--train", type=float, default=0.80)
    parser.add_argument("--eval",  type=float, default=0.10)
    parser.add_argument("--test",  type=float, default=0.10)
    parser.add_argument("--seed",  type=int,   default=42)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if abs(args.train + args.eval + args.test - 1.0) > 1e-6:
        sys.exit("Erreur : train + eval + test doit égaler 1.0")

    if not CHATML_FILE.exists():
        sys.exit(
            f"Fichier introuvable : {CHATML_FILE}\n"
            "Lancer 05_format_chatml.py d'abord."
        )

    print("[STEP 6] Starting stratified split...")
    records = load_jsonl(CHATML_FILE)
    log.info("%d exemples chargés depuis %s", len(records), CHATML_FILE.name)

    # Seed-retry loop (AGENTS.md §4.6 invariant)
    max_retries = 20
    seed = args.seed
    train, eval_, test = [], [], []

    for attempt in range(max_retries):
        train, eval_, test = stratified_split(
            records,
            train_ratio=args.train,
            eval_ratio=args.eval,
            test_ratio=args.test,
            seed=seed,
        )

        missing_train = EXPECTED_STRATA - strata_present(train)
        missing_eval  = EXPECTED_STRATA - strata_present(eval_)
        missing_test  = EXPECTED_STRATA - strata_present(test)

        if not (missing_train or missing_eval or missing_test):
            if attempt > 0:
                log.info("Strates complètes obtenues après %d essai(s) (seed=%d)", attempt + 1, seed)
            break

        log.warning(
            "Seed %d — strates manquantes : train=%d eval=%d test=%d — nouvel essai",
            seed, len(missing_train), len(missing_eval), len(missing_test),
        )
        seed += 1
    else:
        log.error(
            "Impossible d'obtenir les 70 strates dans chaque split après %d essais. "
            "Corpus probablement insuffisant.",
            max_retries,
        )

    write_jsonl(train, DATASETS_DIR / "train.jsonl")
    write_jsonl(eval_,  DATASETS_DIR / "eval.jsonl")
    write_jsonl(test,   DATASETS_DIR / "test.jsonl")

    stats = build_stats(
        records, train, eval_, test,
        seed=seed,
        train_ratio=args.train,
        eval_ratio=args.eval,
        test_ratio=args.test,
    )

    stats_path = DATASETS_DIR / "split_stats.json"
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print(f"[STEP 6] Done. {len(records)} records split into train/eval/test.")
    print(f"  Train : {len(train):>6}  ({args.train*100:.0f}%)")
    print(f"  Eval  : {len(eval_):>6}  ({args.eval*100:.0f}%)")
    print(f"  Test  : {len(test):>6}  ({args.test*100:.0f}%)")
    print(f"  Seed  : {seed}  (initial: {args.seed})")
    print(f"  Stats → {stats_path}")


if __name__ == "__main__":
    main()
