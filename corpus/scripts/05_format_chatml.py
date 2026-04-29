"""
05_format_chatml.py — Conversion du corpus filtré en format ChatML pour Unsloth/QLoRA.

Entrée  : corpus/processed/filtered.jsonl
Sortie  : corpus/datasets/filtered_chatml.jsonl

Format ChatML exact de Mistral Instruct v0.3 (AGENTS.md §4.5) :
  <|im_start|>system
  {SYSTEM_PROMPT}
  <|im_end|>
  <|im_start|>user
  {messages[0].content}
  <|im_end|>
  <|im_start|>assistant
  {messages[1].content}
  <|im_end|>

Le token <|im_end|> final sert de EOS. Unsloth maskera tout jusqu'à (inclus)
<|im_start|>assistant\\n — seul le contenu assistant et le <|im_end|> final
sont backpropagés (train_on_responses_only=True).

Usage :
  python 05_format_chatml.py
  python 05_format_chatml.py --include-counterexamples
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import SYSTEM_PROMPT, CorpusExample

ROOT         = Path(__file__).resolve().parents[1]
FILTERED     = ROOT / "processed" / "filtered.jsonl"
DATASETS_DIR = ROOT / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

# Séquence exacte de tokens (AGENTS.md §4.5) — NE PAS modifier sans mettre à jour
# les tests dans tests/unit/test_chatml_format.py.
_TURN = "<|im_start|>{role}\n{content}\n<|im_end|>"


def to_chatml_text(example: CorpusExample,
                   include_counterexamples: bool = False) -> str | None:
    """
    Convertit un CorpusExample en texte ChatML complet (3 tours : system/user/assistant).
    Retourne None pour les contre-exemples quand include_counterexamples=False.

    Format produit (chaque tour séparé par \\n) :
      <|im_start|>system\\n{SYSTEM_PROMPT}\\n<|im_end|>
      <|im_start|>user\\n{question}\\n<|im_end|>
      <|im_start|>assistant\\n{réponse}\\n<|im_end|>
    """
    if example.is_counterexample and not include_counterexamples:
        return None

    turns = [
        _TURN.format(role="system",    content=SYSTEM_PROMPT),
        _TURN.format(role="user",      content=example.messages[0].content),
        _TURN.format(role="assistant", content=example.messages[1].content),
    ]
    return "\n".join(turns)


def main():
    parser = argparse.ArgumentParser(description="Format ChatML pour fine-tuning")
    parser.add_argument("--include-counterexamples", action="store_true",
                        help="Inclure les contre-exemples (pour DPO)")
    args = parser.parse_args()

    if not FILTERED.exists():
        sys.exit(f"Fichier introuvable : {FILTERED}\nLancer 04_quality_filter.py d'abord.")

    print("[STEP 5] Starting ChatML formatting...")

    records: list[dict] = []
    skipped = 0

    with open(FILTERED, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            d = json.loads(line)
            ex = CorpusExample.from_dict(d)
            text = to_chatml_text(ex, args.include_counterexamples)
            if text is None:
                skipped += 1
                continue
            # Output record fields per AGENTS.md §4.5
            records.append({
                "text":              text,
                "id":                ex.id,
                "atelier":           ex.atelier,
                "secteur":           ex.secteur,
                "source":            ex.source,
                "is_counterexample": ex.is_counterexample,
            })

    out_path = DATASETS_DIR / "filtered_chatml.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"[STEP 5] Done. {len(records)} records written to {out_path}")
    print(f"  {skipped} contre-exemples exclus (utiliser --include-counterexamples pour les inclure)")


if __name__ == "__main__":
    main()
