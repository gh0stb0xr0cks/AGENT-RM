"""
04_quality_filter.py — Filtrage qualité multi-critères du corpus brut.

Portes appliquées dans l'ordre (AGENTS.md §4.4) :
  1.  Structure          : champs requis, 2 messages, rôles user→assistant
  2.  Secteur valide     : secteur ∈ SECTORS
  3.  Atelier valide     : atelier ∈ ATELIERS
  4.  Longueur min       : ≥ min_words dans le tour assistant   (V1+V2 seulement)
  5.  Longueur max       : ≤ max_words dans le tour assistant   (V1+V2 seulement)
  6.  Termes interdits   : 0 occurrence dans le texte complet   (V1+V2 seulement)
  7.  Termes obligatoires: ≥1 terme de REQUIRED_TERMS_BY_ATELIER (V1+V2 seulement)
  8.  Cotation G/V       : SCALE_PATTERN présent (A3/A4/A5, V1+V2 seulement)
  9.  Déduplication      : SHA256(question) unique parmi tous les exemples
  10. source_chunk       : metadata.source_chunk non-None          (V1 seulement)
  11. Question malformée : contenu user ne commence pas par '": ' (V1+V2 seulement)

Volet 3 (is_counterexample=True) : portes 1-3 + 9 uniquement.

Produit :
  - corpus/processed/filtered.jsonl      (exemples acceptés, triés par atelier/secteur/id)
  - corpus/processed/rejected.jsonl      (exemples rejetés + raison)
  - corpus/processed/filter_report.json  (statistiques AGENTS.md §4.4)

Usage :
  python 04_quality_filter.py
  python 04_quality_filter.py --min-words 80 --max-words 2000
  python 04_quality_filter.py --strict
"""
from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from collections import defaultdict
from pathlib import Path

log = logging.getLogger(__name__)

sys.path.insert(0, str(Path(__file__).parent))
from schema import (  # noqa: E402
    ATELIERS,
    FORBIDDEN_TERMS,
    REQUIRED_TERMS_BY_ATELIER,
    SCALE_PATTERN,
    SECTORS,
)

ROOT           = Path(__file__).resolve().parents[1]
RAW_SYNTHETICS = ROOT / "raw" / "synthetics"
PROCESSED_DIR  = ROOT / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

FILTERED_PATH = PROCESSED_DIR / "filtered.jsonl"
REJECTED_PATH = PROCESSED_DIR / "rejected.jsonl"
REPORT_PATH   = PROCESSED_DIR / "filter_report.json"

REQUIRED_FIELDS = {"id", "atelier", "secteur", "source", "messages"}


# ─────────────────────────────────────────────────────────────────────────────
# Fonctions de porte (pure, importables par les tests unitaires)
# ─────────────────────────────────────────────────────────────────────────────

def check_structure(d: dict) -> list[str]:
    """Porte 1 : champs requis + exactement 2 messages (user → assistant)."""
    reasons: list[str] = []
    missing = REQUIRED_FIELDS - d.keys()
    if missing:
        reasons.append(f"missing_fields:{','.join(sorted(missing))}")
        return reasons  # impossible de continuer sans les champs de base

    msgs = d.get("messages", [])
    if len(msgs) != 2:
        reasons.append(f"wrong_msg_count:{len(msgs)}")
    else:
        if msgs[0].get("role") != "user":
            reasons.append("wrong_role_first_message")
        if msgs[1].get("role") != "assistant":
            reasons.append("wrong_role_second_message")
    return reasons


def check_secteur(secteur: str) -> list[str]:
    """Porte 2 : secteur ∈ SECTORS."""
    return [] if secteur in SECTORS else [f"invalid_secteur:{secteur}"]


def check_atelier(atelier: str) -> list[str]:
    """Porte 3 : atelier ∈ ATELIERS."""
    return [] if atelier in ATELIERS else [f"invalid_atelier:{atelier}"]


def check_word_count(answer: str, min_words: int, max_words: int) -> list[str]:
    """Portes 4-5 : longueur de la réponse assistant."""
    wc = len(answer.split())
    if wc < min_words:
        return [f"min_word_count:{wc}"]
    if wc > max_words:
        return [f"max_word_count:{wc}"]
    return []


def check_forbidden_terms(text: str) -> list[str]:
    """Porte 6 : 0 terme interdit dans le texte complet (question + réponse)."""
    lower = text.lower()
    found = [t for t in FORBIDDEN_TERMS if t in lower]
    return [f"forbidden_term:{t}" for t in found]


def check_required_terms(answer: str, atelier: str) -> list[str]:
    """Porte 7 : ≥1 terme obligatoire de REQUIRED_TERMS_BY_ATELIER présent."""
    required = REQUIRED_TERMS_BY_ATELIER.get(atelier, [])
    lower = answer.lower()
    if any(t.lower() in lower for t in required):
        return []
    return ["required_terms:none_found"]


def check_gv_scale(answer: str, atelier: str) -> list[str]:
    """Porte 8 : cotation G/V présente pour A3/A4/A5."""
    if atelier not in ("A3", "A4", "A5"):
        return []
    return [] if SCALE_PATTERN.search(answer) else ["gv_scale_missing"]


def check_duplicate(question: str, seen: set[str]) -> list[str]:
    """Porte 9 : SHA256(question) unique. Ajoute à seen si nouveau."""
    h = hashlib.sha256(question.strip().encode()).hexdigest()
    if h in seen:
        return ["duplicate"]
    seen.add(h)
    return []


def check_source_chunk(metadata: dict) -> list[str]:
    """Porte 10 : source_chunk non-None pour les Volets 1 (anssi_doc)."""
    if metadata.get("source_chunk") is None:
        return ["source_chunk_missing"]
    return []


def check_malformed_question(question: str) -> list[str]:
    """Porte 11 : artefact de parsing — le contenu user commence par '\": '."""
    if question.lstrip().startswith('": '):
        return ["malformed_question"]
    return []


# ─────────────────────────────────────────────────────────────────────────────
# Filtre principal
# ─────────────────────────────────────────────────────────────────────────────

def filter_example(
    d: dict,
    min_words: int,
    max_words: int,
    seen_hashes: set[str],
) -> tuple[bool, list[str]]:
    """
    Applique les portes de l'AGENTS.md §4.4 dans l'ordre.
    Retourne (accepté: bool, raisons_rejet: list[str]).
    Travaille sur le dict brut pour pouvoir rejeter avant from_dict().
    """
    reasons: list[str] = []

    # Porte 1 — structure
    struct_issues = check_structure(d)
    if struct_issues:
        return False, struct_issues  # impossible d'aller plus loin

    # Porte 2-3 — secteur + atelier
    reasons += check_secteur(d["secteur"])
    reasons += check_atelier(d["atelier"])
    if reasons:
        return False, reasons

    is_ce    = d.get("is_counterexample", False)
    source   = d.get("source", "")
    msgs     = d["messages"]
    question = msgs[0]["content"]
    answer   = msgs[1]["content"]
    metadata = d.get("metadata", {})
    atelier  = d["atelier"]
    full_text = question + " " + answer

    # Porte 9 — déduplication (appliquée à tous, y compris Volet 3)
    reasons += check_duplicate(question, seen_hashes)

    if is_ce:
        # Volet 3 : portes 1-3 + 9 uniquement
        if not d.get("error_type"):
            reasons.append("counterexample_missing_error_type")
        return len(reasons) == 0, reasons

    # Portes Volet 1 + 2 uniquement
    reasons += check_word_count(answer, min_words, max_words)
    reasons += check_forbidden_terms(full_text)
    reasons += check_required_terms(answer, atelier)
    reasons += check_gv_scale(answer, atelier)
    reasons += check_malformed_question(question)

    # Porte 10 — source_chunk (Volet 1 seulement)
    if source == "anssi_doc":
        reasons += check_source_chunk(metadata)

    return len(reasons) == 0, reasons


# ─────────────────────────────────────────────────────────────────────────────
# Chargement en streaming
# ─────────────────────────────────────────────────────────────────────────────

def iter_jsonl(path: Path):
    """Générateur ligne-par-ligne (évite de charger tout en RAM)."""
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("%s ligne %d : JSON invalide — %s", path.name, lineno, e)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Filtrage qualité du corpus EBIOS RM (AGENTS.md §4.4)"
    )
    parser.add_argument("--min-words", type=int, default=80,
                        help="Nombre minimum de mots dans la réponse (défaut: 80)")
    parser.add_argument("--max-words", type=int, default=2000,
                        help="Nombre maximum de mots dans la réponse (défaut: 2000)")
    parser.add_argument("--strict", action="store_true",
                        help="Exit 1 sur tout avertissement (pas seulement erreurs)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    print("[STEP 4] Starting quality filter...")

    jsonl_files = sorted(RAW_SYNTHETICS.glob("*.jsonl"))
    if not jsonl_files:
        log.error("Aucun fichier JSONL dans %s", RAW_SYNTHETICS)
        sys.exit(1)

    seen_hashes: set[str]  = set()
    accepted_dicts: list[dict] = []
    rejected_records: list[dict] = []

    # Counters for the spec-compliant report
    rejected_by_gate: dict[str, int] = defaultdict(int)
    accepted_by_volet: dict[str, int] = defaultdict(int)
    accepted_by_atelier: dict[str, int] = defaultdict(int)
    accepted_by_sector: dict[str, int] = defaultdict(int)
    total_input = 0
    total_warnings = 0

    for path in jsonl_files:
        log.info("Chargement : %s", path.name)
        for d in iter_jsonl(path):
            total_input += 1
            ok, reasons = filter_example(
                d,
                min_words=args.min_words,
                max_words=args.max_words,
                seen_hashes=seen_hashes,
            )
            if ok:
                accepted_dicts.append(d)
                volet = (
                    "counterexample" if d.get("is_counterexample")
                    else d.get("source", "unknown")
                )
                accepted_by_volet[volet]    += 1
                accepted_by_atelier[d.get("atelier", "?")] += 1
                accepted_by_sector[d.get("secteur", "?")]  += 1
            else:
                for r in reasons:
                    gate_key = r.split(":")[0]
                    rejected_by_gate[gate_key] += 1
                rec = dict(d)
                rec["rejection_reasons"] = reasons
                rejected_records.append(rec)

    total_accepted = len(accepted_dicts)
    total_rejected = len(rejected_records)

    # Sort accepted by (atelier, secteur, id)
    accepted_dicts.sort(key=lambda d: (d.get("atelier",""), d.get("secteur",""), d.get("id","")))

    # Write filtered.jsonl
    with open(FILTERED_PATH, "w", encoding="utf-8") as f:
        for d in accepted_dicts:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # Write rejected.jsonl
    with open(REJECTED_PATH, "w", encoding="utf-8") as f:
        for rec in rejected_records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Build spec-compliant report (AGENTS.md §4.4)
    report = {
        "total_input":    total_input,
        "total_accepted": total_accepted,
        "rejected_by_gate": dict(sorted(rejected_by_gate.items(), key=lambda x: -x[1])),
        "accepted_by_volet":   dict(sorted(accepted_by_volet.items())),
        "accepted_by_atelier": dict(sorted(accepted_by_atelier.items())),
        "accepted_by_sector":  dict(sorted(accepted_by_sector.items())),
    }

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    # Summary
    rate = round(total_accepted / total_input * 100, 1) if total_input else 0
    print(f"[STEP 4] Done. {total_accepted} records written to {FILTERED_PATH}")
    print(f"  Total input   : {total_input}")
    print(f"  Accepted      : {total_accepted} ({rate}%)")
    print(f"  Rejected      : {total_rejected}")
    if rejected_by_gate:
        print("  Rejected by gate :")
        for gate, n in report["rejected_by_gate"].items():
            print(f"    {gate:35s} : {n}")
    print(f"  Report → {REPORT_PATH}")

    # Exit code (AGENTS.md §4.4)
    if total_accepted < 8000:
        if args.strict:
            total_warnings += 1
        log.warning(
            "Seuil minimum non atteint : %d acceptés < 8 000 requis", total_accepted
        )

    exit_code = 1 if (total_accepted < 8000 or (args.strict and total_warnings > 0)) else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
