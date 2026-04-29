---
paths:
  - corpus/**
  - tests/unit/test_corpus_quality.py
  - tests/unit/test_schema.py
  - tests/integration/test_pipeline.py
---

# AGENTS.md — `corpus/` Module
## Design Specifications for Claude Code

> **Read this file completely before touching any file under `corpus/`.**
> This document is the binding specification. If it conflicts with the existing
> code, fix the code. If it conflicts with your assumptions, fix your assumptions.

---

## 0. Absolute Rules (checked on every write)

These rules are non-negotiable. A pre-write hook in `.claude/settings.json`
runs `scripts/check_terminology.py` on every file you save under `corpus/`.

```
NEVER write in any .py or .jsonl file under corpus/:
  "biens essentiels"      →  use "valeurs métier"
  "actifs"                →  use "biens supports"
  "menaces"               →  use "sources de risque"
  "PACS"                  →  use "plan de traitement du risque"
  "risque brut"           →  use "risque initial"
  "risque net"            →  use "risque résiduel"
  "probabilité"           →  use "vraisemblance"
  "impact"                →  use "gravité"  (in EBIOS RM context)
  "biens essentiels"      →  use "valeurs métier"
```

Exception: the strings above MAY appear as dict keys in `FORBIDDEN_TERMS`
inside `schema.py` (where they are labelled as wrong by design).

**Do not redefine any constant from `schema.py` in any other file.**
Import. Never copy.

---

## 1. Module Context

The `corpus/` module produces three JSONL dataset files consumed by
`training/finetune.py`. It is the **only write layer** in the data path.
All other modules are consumers.

```
corpus/                          training/
  datasets/train.jsonl    ──────▶  finetune.py (QLoRA)
  datasets/eval.jsonl     ──────▶  finetune.py (loss monitoring)
  datasets/test.jsonl     ──────▶  eval_ebios.py (held-out benchmark)
```

Outside the corpus module, these modules also import from `schema.py`:

```
orchestration/guardrails/    → FORBIDDEN_TERMS, SCALE_PATTERN
tests/unit/test_schema.py    → all symbols (contract test)
tests/ebios/                 → REQUIRED_TERMS_BY_ATELIER, SCALE_PATTERN
```

---

## 2. File Map and Ownership

Each file below has exactly one owner. Do not move responsibilities between files.

```
corpus/
├── scripts/
│   ├── schema.py                ← SOURCE OF TRUTH. Owner: schema.py only.
│   ├── 01_extract_pdf.py        ← Owner: PDF extraction + chunking
│   ├── 02_generate_synthetics.py← Owner: Volet 2 generation (multi-backend)
│   ├── 03_generate_counterexamples.py ← Owner: Volet 3 mutations
│   ├── 04_quality_filter.py     ← Owner: all quality gates
│   ├── 05_format_chatml.py      ← Owner: ChatML serialisation
│   ├── 06_stratified_split.py   ← Owner: train/eval/test split
│   └── 07_validate_corpus.py    ← Owner: final gate, called by Makefile
│
├── raw/
│   ├── anssi/                   ← READ-ONLY after 01. Never write here from 02-07.
│   ├── mitre/                   ← READ-ONLY after 01.
│   └── synthetics/              ← Written by 02 and 03. Read by 04.
│       ├── {atelier}_{secteur}.jsonl  (70 files, one per workshop × sector)
│       └── counterexamples.jsonl
│
├── processed/
│   ├── merged.jsonl             ← Written by 04 (pre-filter concatenation)
│   └── filtered.jsonl           ← Written by 04 (post-filter output)
│
└── datasets/
    ├── train.jsonl              ← Written by 06. READ-ONLY after that.
    ├── eval.jsonl               ← Written by 06. READ-ONLY after that.
    ├── test.jsonl               ← Written by 06. READ-ONLY after that.
    └── split_stats.json         ← Written by 06.
```

**Path constants.** Every script resolves paths relative to its own location
using `Path(__file__).resolve().parents[N]`. Never use `os.getcwd()`.
The canonical pattern is:

```python
ROOT = Path(__file__).resolve().parents[1]   # → corpus/
SCRIPTS_DIR = ROOT / "scripts"
RAW_DIR = ROOT / "raw"
PROCESSED_DIR = ROOT / "processed"
DATASETS_DIR = ROOT / "datasets"
```

---

## 3. `schema.py` — Contract Specification

`schema.py` is the only file in the project allowed to define EBIOS RM
domain constants. All other files import from it. If you need a new
constant, add it to `schema.py` first, then import it.

### 3.1 Required exports (contract — do not remove or rename)

| Symbol | Type | Description |
|---|---|---|
| `ATELIERS` | `list[str]` | `["A1","A2","A3","A4","A5"]` |
| `SECTORS` | `list[str]` | 14 sector codes (lowercase, no accents) |
| `SECTOR_LABELS` | `dict[str,str]` | Human-readable sector descriptions for prompts |
| `SYSTEM_PROMPT` | `str` | Canonical EBIOS RM 2024 assistant system prompt |
| `FORBIDDEN_TERMS` | `dict[str,str]` | `{wrong_term: correct_term}` — keys lowercase |
| `REQUIRED_TERMS_BY_ATELIER` | `dict[str,list[str]]` | Min terms per workshop |
| `SCALE_PATTERN` | `re.Pattern` | `re.compile(r'\b(G[1-4]\|V[1-4])\b')` |
| `GENERATION_TEMPLATES` | `dict[str,str]` | One prompt template per workshop |
| `GENERATION_THEMES` | `dict[str,list[str]]` | ≥26 themes per workshop |
| `CorpusExample` | `dataclass` | See §3.2 |
| `Message` | `dataclass` | `role: Literal["system","user","assistant"]`, `content: str` |

### 3.2 `CorpusExample` dataclass — exact field specification

```python
@dataclass
class CorpusExample:
    id: str                    # Format: "{atelier}_{secteur}_{index:04d}"
                               # Example: "a3_sante_0042"
    atelier: Literal["A1","A2","A3","A4","A5"]
    secteur: str               # Must be a value from SECTORS
    source: Literal[
        "anssi_doc",           # Volet 1 — derived from official ANSSI PDF
        "synthetic",           # Volet 2 — LLM-generated
        "counterexample",      # Volet 3 — mutated from synthetic
    ]
    messages: list[Message]    # Always exactly 2: user + assistant
                               # (system is added by 05_format_chatml.py)
    metadata: dict             # See §3.3 for required keys by source
    is_counterexample: bool = False
    error_type: str | None = None  # Required when is_counterexample=True
```

Invariants enforced by `07_validate_corpus.py`:
- `len(messages) == 2`
- `messages[0].role == "user"`
- `messages[1].role == "assistant"`
- `secteur in SECTORS`
- `atelier in ATELIERS`
- If `source == "counterexample"`: `is_counterexample == True` and `error_type is not None`
- If `is_counterexample == True`: `source == "counterexample"`

### 3.3 `metadata` field — required keys by source

**Volet 1** (`source == "anssi_doc"`):
```python
metadata = {
    "source_chunk": str,          # chunk ID from raw/anssi/index.jsonl — REQUIRED
    "source_document": str,       # e.g. "guide_ebios_rm_2024"
    "word_count": int,            # word count of assistant turn
    "has_gv_scale": bool,         # True if SCALE_PATTERN matches assistant turn
}
```

**Volet 2** (`source == "synthetic"`):
```python
metadata = {
    "source_chunk": None,         # always None for Volet 2
    "generation_theme": str,      # the theme string used in the prompt
    "generation_backend": str,    # "ollama" | "claude" | "mistral" | "openrouter"
    "generation_model": str,      # exact model identifier
    "word_count": int,
    "has_gv_scale": bool,
}
```

**Volet 3** (`source == "counterexample"`):
```python
metadata = {
    "source_chunk": None,
    "parent_id": str,             # id of the Volet 2 example that was mutated
    "mutation_strategy": str,     # same as error_type
    "word_count": int,
    "has_gv_scale": bool,         # may be False (wrong_scale mutation removes it)
}
```

### 3.4 `GENERATION_TEMPLATES` — interface contract

Each template has **exactly two placeholders**: `{secteur}` and `{theme}`.
No other placeholders are allowed. The caller does:

```python
prompt = GENERATION_TEMPLATES[atelier].format(secteur=sector_label, theme=theme_str)
```

The template MUST instruct the LLM to respond with a JSON object:
```json
{"question": "...", "reponse": "..."}
```
and nothing else (no markdown fences, no preamble).

Do not add new placeholders to templates without updating
`02_generate_synthetics.py` and all tests.

---

## 4. Step-by-Step Script Specifications

### 4.1 `01_extract_pdf.py`

**Responsibility.** Extract text from source PDFs, clean it, chunk it,
write an index.

**CLI interface:**
```
python 01_extract_pdf.py [--source anssi|mitre|all]
```
Default: `--source all`.

**Processing per PDF:**
1. Extract with `pdfplumber` (preferred) or `pypdf` fallback.
2. Clean: collapse 3+ newlines → 2, collapse multiple spaces → 1,
   remove form feeds.
3. Chunk at paragraph boundaries, targeting ~800 tokens (~3,200 chars)
   with 80-token (320-char) overlap.
4. Write `<docname>.txt` alongside the PDF.

**Output — `corpus/raw/anssi/index.jsonl`:**
One JSONL record per chunk:
```python
{
    "chunk_id": "guide_ebios_rm_2024_0017",  # "{doc_id}_{index:04d}"
    "doc_id": "guide_ebios_rm_2024",
    "source": "anssi",                        # or "mitre"
    "page_range": [3, 5],                     # [first_page, last_page]
    "tokens_approx": 782,
    "text": "..."
}
```

**Error handling.** Log errors per file but continue processing other
files. Never exit on a single PDF failure. Print a summary at the end:
`N files processed, M chunks extracted, K errors`.

**Dependencies:** `pdfplumber`. Install check at top of script:
```python
try:
    import pdfplumber
except ImportError:
    sys.exit("pip install pdfplumber")
```

---

### 4.2 `02_generate_synthetics.py`

**Responsibility.** Generate Volet 2 Q/A pairs via LLM backends.

**CLI interface:**
```
python 02_generate_synthetics.py \
    [--backend ollama|claude|mistral|openrouter] \
    [--model MODEL_ID] \
    [--atelier A1|A2|A3|A4|A5] \
    [--secteur SECTEUR] \
    [--count N] \
    [--delay SECONDS] \
    [--max-retries N] \
    [--workers N] \
    [--resume]
```

**Generation targets per (workshop × sector):**
```python
TARGET_PER_ATELIER_SECTEUR = {
    "A1": 18,   # × 14 sectors = 252
    "A2": 22,   # × 14 sectors = 308
    "A3": 55,   # × 14 sectors = 770
    "A4": 55,   # × 14 sectors = 770
    "A5": 28,   # × 14 sectors = 392
}
# Base total: 2,492. Additional passes with --scale reach ~7,000.
```

**Progress checkpointing.** After each shard completes, write:
```
corpus/raw/.generation_progress.json
{
    "a3_sante": {"generated": 55, "target": 55, "last_updated": "ISO8601"},
    ...
}
```
`--resume` skips shards where `generated >= target`.

**Backend interface.** Each backend must implement:
```python
def generate(prompt: str, system: str, temperature: float = 0.7) -> str:
    """Returns the raw LLM text response. Raises on network/API error."""
```

**Response parsing.** Try JSON first, fall back to heuristic extraction:
```python
def parse_response(raw: str) -> tuple[str, str] | None:
    """
    Returns (question, reponse) or None if unparseable.
    Strategy:
      1. Strip markdown fences (```json...```).
      2. json.loads() the result.
      3. Extract keys "question" and "reponse" (accept "response" as alias).
      4. If JSON fails: split on the first "?" — everything before is question,
         everything after is answer. Only accept if both parts > 20 words.
      5. Return None if both strategies fail.
    """
```

**ID generation:**
```python
def make_id(atelier: str, secteur: str, index: int) -> str:
    return f"{atelier.lower()}_{secteur}_{index:04d}"
```

**Output per shard:**
`corpus/raw/synthetics/{atelier}_{secteur}.jsonl`
One `CorpusExample.to_dict()` per line, UTF-8.

**Retry policy.** On API error: exponential backoff, base 2s, max 3 retries.
On parse failure: try with a different theme (rotate), max 2 attempts.
After both fail: log a warning, skip the example, continue.

**Default backends:**
- `ollama`: `http://localhost:11434` — model default `mistral`
- `claude`: requires `ANTHROPIC_API_KEY` — model default `claude-sonnet-4-20250514`
- `mistral`: requires `MISTRAL_API_KEY`
- `openrouter`: requires `OPENROUTER_API_KEY` — model default `mistralai/mistral-small-3.1`

---

### 4.3 `03_generate_counterexamples.py`

**Responsibility.** Generate Volet 3 by mutating Volet 2 examples.

**CLI interface:**
```
python 03_generate_counterexamples.py \
    [--count N]                      # total counterexamples to generate (default: 1500)
    [--error-type TYPE]              # generate only one error type
    [--seed N]                       # random seed (default: 42)
```

**Error type distribution** (when `--count 1500`, default):
```python
ERROR_DISTRIBUTION = {
    "forbidden_term":    300,
    "wrong_scale":       300,
    "wrong_methodology": 300,
    "incomplete_answer": 300,
    "hallucinated_rule": 300,
}
```

**Five mutation functions — exact contracts:**

```python
def mutate_forbidden_term(answer: str) -> tuple[str, str]:
    """
    Replace one ANSSI correct term with its forbidden EBIOS 2010 equivalent.
    Source: invert schema.FORBIDDEN_TERMS {wrong→correct} to {correct→wrong}.
    Replace only the FIRST occurrence (to avoid over-mutation).
    If no replaceable term found: append "Les menaces identifiées sont prioritaires."
    Returns: (mutated_answer, "forbidden_term")
    """

def mutate_wrong_scale(answer: str) -> tuple[str, str]:
    """
    Replace G/V notation with informal descriptions.
    Rules: G([1-4]) → "niveau \1",  V([1-4]) → "vraisemblance \1"
    If no G/V found: append "Le niveau de risque est estimé à 3/5."
    Returns: (mutated_answer, "wrong_scale")
    """

def mutate_wrong_methodology(answer: str) -> tuple[str, str]:
    """
    Inject a confusion phrase referencing ISO 27005 or EBIOS 2010.
    Choose randomly from a list of at least 4 confusion phrases.
    ALWAYS appends (never replaces) to preserve answer length.
    Returns: (mutated_answer, "wrong_methodology")
    """

def mutate_incomplete_answer(answer: str) -> tuple[str, str]:
    """
    Truncate the answer at the first G/V scale mention.
    Pattern: search for SCALE_PATTERN in answer.
      - If found: answer[:match.start()].rstrip() + "\n\n[À compléter.]"
      - If not found: answer[:len(answer)//2] + "\n\n[À compléter.]"
    Returns: (mutated_answer, "incomplete_answer")
    """

def mutate_hallucinated_rule(answer: str) -> tuple[str, str]:
    """
    Append a plausible-sounding but invented ANSSI/EBIOS RM rule.
    The hallucination must sound official and specific (cite an article,
    annex, or delay). Choose from a list of ≥5 pre-written hallucinations.
    ALWAYS appends. Never modifies existing content.
    Returns: (mutated_answer, "hallucinated_rule")
    """
```

**Source selection.** Load all Volet 2 shards from `raw/synthetics/`,
excluding `counterexamples.jsonl`. Sample uniformly across shards,
respecting the stratification target (equal distribution across
workshops and sectors).

**Output:** `corpus/raw/synthetics/counterexamples.jsonl`
Each record is a `CorpusExample.to_dict()` with:
- `source = "counterexample"`
- `is_counterexample = True`
- `error_type = "<type>"`
- `metadata.parent_id` = id of the source Volet 2 example
- `metadata.mutation_strategy` = same as `error_type`
- **question is unchanged** — only the assistant turn is mutated.

---

### 4.4 `04_quality_filter.py`

**Responsibility.** Apply all quality gates and produce `filtered.jsonl`.

**CLI interface:**
```
python 04_quality_filter.py \
    [--min-words N]      # default: 80
    [--max-words N]      # default: 2000
    [--strict]           # exit 1 on any warning (not just errors)
```

**Input.** Reads all JSONL files from `raw/synthetics/` (Volets 1, 2, 3).

**Gates applied in order:**

| Gate | Applied to | Threshold | Action on fail |
|---|---|---|---|
| Valid JSON parse | All | Must parse without error | REJECT + log |
| Required fields | All | id, atelier, secteur, source, messages | REJECT + log |
| Secteur valid | All | Must be in `SECTORS` | REJECT + log |
| Atelier valid | All | Must be in `ATELIERS` | REJECT + log |
| Message count | All | Exactly 2 messages | REJECT + log |
| Message roles | All | user then assistant | REJECT + log |
| Min word count | Volets 1 & 2 | ≥ 80 words in assistant turn | REJECT |
| Max word count | Volets 1 & 2 | ≤ 2,000 words in assistant turn | REJECT |
| Forbidden terms | Volets 1 & 2 | 0 matches in full text | REJECT + log term |
| Required terms | Volets 1 & 2 | ≥1 from `REQUIRED_TERMS_BY_ATELIER[atelier]` | REJECT |
| G/V scale | Volets 1 & 2, A3/A4/A5 | `SCALE_PATTERN` must match assistant turn | REJECT |
| Deduplication | All | SHA256 of question text must be unique | REJECT duplicate |
| source_chunk set | Volet 1 only | `metadata.source_chunk` must not be None | REJECT |

**Volet 3 exemption.** Counter-examples (`is_counterexample == True`) skip the
forbidden-terms, required-terms, G/V scale, and word count gates. They
are validated only for structure (fields, roles, error_type present).

**Output:**
- `corpus/processed/filtered.jsonl` — all passing records, sorted by
  `(atelier, secteur, id)`.
- `corpus/processed/filter_report.json`:
```json
{
  "total_input": 10500,
  "total_accepted": 9800,
  "rejected_by_gate": {
    "forbidden_term": 45,
    "min_word_count": 120,
    "gv_scale_missing": 30,
    "duplicate": 15
  },
  "accepted_by_volet": {
    "anssi_doc": 1450,
    "synthetic": 6900,
    "counterexample": 1450
  },
  "accepted_by_atelier": {"A1": ..., "A2": ..., ...},
  "accepted_by_sector": {"sante": ..., ...}
}
```

**Exit code.** 0 if `total_accepted >= 8000`, else 1.

---

### 4.5 `05_format_chatml.py`

**Responsibility.** Convert each `CorpusExample` to a ChatML text string
for consumption by Unsloth/TRL SFTTrainer.

**CLI interface:**
```
python 05_format_chatml.py [--include-counterexamples]
```

**ChatML format.** The exact token sequence for Mistral Instruct v0.3:
```
<|im_start|>system
{SYSTEM_PROMPT}
<|im_end|>
<|im_start|>user
{messages[0].content}
<|im_end|>
<|im_start|>assistant
{messages[1].content}
<|im_end|>
```

Note: the trailing `<|im_end|>` after the assistant turn is the EOS token.
Unsloth's `train_on_responses_only=True` will mask everything up to and
including the `<|im_start|>assistant\n` token — only the assistant content
and the final `<|im_end|>` are backpropagated.

**Output record format** (one per line in `datasets/train_chatml.jsonl`):
```python
{
    "text": "<|im_start|>system\n...",   # the full ChatML string
    "id": "a3_sante_0042",               # preserved for debugging
    "atelier": "A3",
    "secteur": "sante",
    "source": "synthetic",
    "is_counterexample": False,
}
```

**Counter-example handling.** Excluded by default. With
`--include-counterexamples`, included as-is. The DPO pairing script
(outside corpus module) is responsible for forming `(chosen, rejected)`
pairs from parent and counterexample records.

---

### 4.6 `06_stratified_split.py`

**Responsibility.** Produce the three final dataset files with guaranteed
stratification across `(atelier, secteur)`.

**CLI interface:**
```
python 06_stratified_split.py \
    [--train FLOAT]   # default: 0.80
    [--eval FLOAT]    # default: 0.10
    [--test FLOAT]    # default: 0.10
    [--seed INT]      # default: 42
```

**Stratification algorithm.**
```
For each stratum (atelier, secteur):
  1. Shuffle the stratum's records (RNG seeded with --seed).
  2. n_test  = max(1, floor(n * test_ratio))
  3. n_eval  = max(1, floor(n * eval_ratio))
  4. n_train = n - n_test - n_eval
  5. If n < 3: assign all to train (log a warning).
  6. Append to the respective global lists.
Shuffle each global list after assembly.
```

**Invariant.** After splitting, every (atelier, secteur) stratum must
appear in all three splits. `07_validate_corpus.py` checks this.
If any stratum is absent from train/eval/test, the split must be retried
with a different seed.

**Output:**
- `datasets/train.jsonl`
- `datasets/eval.jsonl`
- `datasets/test.jsonl`
- `datasets/split_stats.json`:
```json
{
  "seed": 42,
  "ratios": {"train": 0.80, "eval": 0.10, "test": 0.10},
  "totals": {"train": 7840, "eval": 980, "test": 980},
  "by_atelier": {
    "A1": {"train": 201, "eval": 25, "test": 26},
    ...
  },
  "by_stratum": {
    "A1_sante": {"train": 14, "eval": 2, "test": 2},
    ...
  }
}
```

---

### 4.7 `07_validate_corpus.py`

**Responsibility.** Final gate. Called by `make validate` and as a
prerequisite of `make train`. Exit 0 = pass, exit 1 = fail.

**CLI interface:**
```
python 07_validate_corpus.py [--strict]
```

**Checks performed (in order):**

1. **File existence.** All three dataset files exist and are non-empty.
2. **Minimum counts.**
   - `train.jsonl`: ≥ 7,000 examples
   - `eval.jsonl`: ≥ 800 examples
   - `test.jsonl`: ≥ 800 examples
3. **Stratum coverage.** All 70 (atelier × sector) combinations present
   in each of the three files.
4. **Zero forbidden terms** in Volet 1 and Volet 2 examples (re-checked
   on the final files, not just on filtered.jsonl).
5. **G/V scale presence** in all A3/A4/A5 Volet 1 and 2 examples
   across all three splits.
6. **Counter-example rate.** Volet 3 examples must not exceed 20% of
   `train.jsonl` (prevents alignment training from dominating SFT).
7. **No metadata regression.** Every example must have all required
   metadata keys for its source type (§3.3).
8. **ID uniqueness** across all three files combined.
9. **Split leakage.** No ID appears in more than one split.

**Output:**
```
corpus/processed/validation_report.json
{
  "status": "PASS" | "FAIL",
  "checks": {
    "file_existence": true,
    "min_counts": {"train": true, "eval": true, "test": true},
    "stratum_coverage": {"train": true, "eval": false, ...},
    ...
  },
  "errors": ["..."],
  "warnings": ["..."]
}
```

Print a human-readable summary to stdout. In strict mode (`--strict`),
warnings also cause exit 1.

---

## 5. Tests — Required Coverage

All tests live under `tests/`. Run with `pytest -x tests/`.

### 5.1 `tests/unit/test_schema.py`

Tests for `schema.py`. Must pass with no LLM or network access.

```python
# Required test cases:
def test_ateliers_is_list_of_five():
def test_sectors_has_14_entries():
def test_sector_labels_keys_match_sectors():
def test_system_prompt_contains_required_terms():
    # Check all of: "valeurs métier", "biens supports", "sources de risque",
    # "plan de traitement du risque", "G1", "G4", "V1", "V4"
def test_forbidden_terms_keys_are_lowercase():
def test_forbidden_terms_values_are_different_from_keys():
def test_generation_templates_have_exactly_two_placeholders():
    # {secteur} and {theme} must be present, nothing else
    # Use string.Formatter().parse() to extract field names
def test_generation_themes_has_at_least_26_per_atelier():
def test_scale_pattern_matches_valid_codes():
    # G1, G2, G3, G4, V1, V2, V3, V4 must all match
def test_scale_pattern_rejects_invalid_codes():
    # G5, V0, G0, V5 must NOT match
def test_corpus_example_roundtrip():
    # Build a CorpusExample, call to_dict(), call from_dict(), assert equal
def test_corpus_example_id_format():
    # id must match r"^[a-z][0-9]_[a-z]+_\d{4}$"
def test_message_roles_are_literal():
    # Only "system", "user", "assistant" are valid
```

### 5.2 `tests/unit/test_corpus_quality.py`

Tests for the filter logic in `04_quality_filter.py`. All tests use
in-memory examples — no file I/O.

```python
# Import the filter functions directly (not via subprocess)
from corpus.scripts.quality_filter import (
    check_word_count, check_forbidden_terms,
    check_required_terms, check_gv_scale,
    check_duplicate, check_structure,
)

def test_reject_forbidden_term_in_assistant_turn():
    # Example with "biens essentiels" in answer → rejected
def test_accept_correct_term_in_assistant_turn():
    # Example with "valeurs métier" → accepted
def test_reject_too_short_answer():
    # < 80 words in assistant turn → rejected
def test_reject_too_long_answer():
    # > 2000 words → rejected
def test_reject_missing_gv_scale_in_a3():
    # A3 example with no G/V notation → rejected
def test_accept_gv_scale_in_a3():
    # A3 example with "G3" and "V2" → accepted
def test_accept_missing_gv_scale_in_a1():
    # A1 example without G/V → accepted (not required for A1/A2)
def test_reject_duplicate_question():
    # Two examples with identical question text → second rejected
def test_counterexample_skips_forbidden_term_gate():
    # Counter-example with "biens essentiels" → NOT rejected
    # (is_counterexample=True exempts it)
def test_reject_invalid_secteur():
    # secteur="unknown" → rejected
def test_reject_missing_source_chunk_for_volet1():
    # source="anssi_doc", metadata.source_chunk=None → rejected
```

### 5.3 `tests/unit/test_mutations.py`

Tests for `03_generate_counterexamples.py` mutation functions.

```python
def test_mutate_forbidden_term_changes_answer():
def test_mutate_forbidden_term_preserves_question():
def test_mutate_wrong_scale_removes_gv_notation():
    # After mutation: SCALE_PATTERN.search(mutated) should find none
    # OR returns notation like "niveau 3" instead of "G3"
def test_mutate_wrong_methodology_appends_only():
    # Original text still present in mutated answer
def test_mutate_incomplete_answer_is_shorter():
    # len(mutated) < len(original)
def test_mutate_hallucinated_rule_appends_only():
def test_all_mutations_preserve_question():
    # All five mutation functions: question turn unchanged
def test_error_type_matches_mutation():
    # Each function returns the correct error_type string
```

### 5.4 `tests/unit/test_chatml_format.py`

Tests for `05_format_chatml.py`.

```python
def test_chatml_contains_system_prompt():
def test_chatml_starts_with_im_start_system():
def test_chatml_ends_with_im_end():
    # Final token must be <|im_end|>
def test_chatml_has_three_turns():
    # Count "<|im_start|>" occurrences → must be exactly 3
def test_counterexample_excluded_by_default():
def test_counterexample_included_with_flag():
```

### 5.5 `tests/integration/test_pipeline.py`

Integration test: runs the full 7-step pipeline on a micro-corpus
(3 synthetic examples per stratum × 5 workshops × 14 sectors = 210
examples). No LLM is called — examples are loaded from fixtures.

```python
@pytest.fixture
def micro_corpus(tmp_path):
    """
    Write 210 minimal valid CorpusExamples to tmp_path/raw/synthetics/
    (3 per atelier × sector stratum) and return tmp_path.
    """

def test_filter_accepts_all_valid_examples(micro_corpus):
def test_split_covers_all_strata(micro_corpus):
def test_validate_passes_on_clean_corpus(micro_corpus):
def test_validate_fails_on_forbidden_term(micro_corpus):
    # Inject one example with "biens essentiels" → validate must exit 1
def test_validate_fails_below_minimum_count(micro_corpus):
    # With only 210 examples: validate must exit 1 on min count check
```

---

## 6. Makefile Targets

The root `Makefile` exposes these corpus-related targets.
When implementing a new target, ensure idempotency (running twice
produces the same output).

```makefile
make build-corpus        # Steps 04→07 (assumes 02+03 already ran)
make generate            # Step 02 only (--backend ollama, air-gapped)
make generate-bootstrap  # Step 02 via Claude API (M2 bootstrap phase)
make counterexamples     # Step 03 only
make filter              # Step 04 only
make format              # Step 05 only
make split               # Step 06 only
make validate            # Step 07 only
make validate-strict     # Step 07 with --strict
make corpus-stats        # Print line counts for all JSONL files
make clean-corpus        # Delete generated files, keep raw/anssi and raw/mitre
```

Each target that modifies files must print:
```
[STEP N] Starting <step name>...
[STEP N] Done. <N> records written to <path>.
```

---

## 7. Coding Standards

### 7.1 Style

- Python 3.11+.
- Type annotations on all public functions and dataclass fields.
- Use `from __future__ import annotations` at the top of every script.
- `ruff check .` must pass with zero warnings.
- Line length: 100 characters.

### 7.2 Logging

Use `logging` module (not `print`) for operational messages. Reserve
`print` for user-facing progress (tqdm bars, final summaries).

```python
import logging
log = logging.getLogger(__name__)
# Root configuration set in main() only:
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
```

### 7.3 File I/O

- Always open files with `encoding="utf-8"`.
- Always use `ensure_ascii=False` in `json.dumps`.
- Never load an entire large JSONL into RAM at once if the file could
  exceed 100MB. Stream line-by-line.

```python
# Correct streaming pattern:
def iter_jsonl(path: Path):
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)
```

### 7.4 Randomness

Always seed RNG explicitly. Never use `random.seed()` at module level.
Pass seeds down from `main()`:

```python
rng = random.Random(seed)   # use rng.shuffle(), rng.choice(), etc.
```

### 7.5 Error handling in generation scripts

- On API error: catch and retry with exponential backoff. Log at WARNING.
- On parse error: log at WARNING, increment a counter, continue.
- If error rate > 30% within a shard: log at ERROR, halt that shard,
  continue with the next.
- Never silently swallow exceptions.

### 7.6 Imports

Absolute rule: no circular imports. Import order:
1. stdlib
2. third-party
3. local (`schema`, other corpus scripts)

`schema.py` imports nothing from the corpus pipeline. All other scripts
import from `schema`. None of the `01–07` scripts import from each other.

---

## 8. Environment Variables

Scripts must read credentials from environment variables only.
Never hardcode or default to a real key.

| Variable | Used by | Required for |
|---|---|---|
| `ANTHROPIC_API_KEY` | `02_generate_synthetics.py` | `--backend claude` |
| `MISTRAL_API_KEY` | `02_generate_synthetics.py` | `--backend mistral` |
| `OPENROUTER_API_KEY` | `02_generate_synthetics.py` | `--backend openrouter` |

If the required key is missing and the backend is selected, exit immediately:
```python
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    sys.exit("ANTHROPIC_API_KEY is not set. Export it before running with --backend claude.")
```

For `--backend ollama`, no key is required. The host defaults to
`http://localhost:11434` and can be overridden with `OLLAMA_HOST`.

---

## 9. What Claude Code Must NOT Do

- **Do not add a `--dry-run` flag** without also adding a test that
  confirms the flag produces zero file writes.
- **Do not invent new EBIOS RM terminology** in templates or prompts.
  All ANSSI terms must come from the official 2024 guide. If in doubt,
  do not add the term.
- **Do not modify `datasets/test.jsonl` after it is written.** This file
  is the held-out benchmark. Adding examples to it during a re-run
  would contaminate the benchmark.
- **Do not add logging to the `schema.py` module.** It is a pure data
  module. No side effects.
- **Do not call `sys.exit()` from inside a function.** Only call it from
  `main()` or the `if __name__ == "__main__"` block.
- **Do not use `open(..., "w")` on `raw/anssi/` or `raw/mitre/` from any
  script other than `01_extract_pdf.py`.** These directories are read-only
  after step 1.
- **Do not write `is_counterexample: true` examples to Volet 2 shards.**
  Counter-examples belong only in `counterexamples.jsonl`.

---

## 10. Acceptance Criteria

A corpus build passes when ALL of the following are true:

```
pytest tests/unit/test_schema.py         → 0 failures
pytest tests/unit/test_corpus_quality.py → 0 failures
pytest tests/unit/test_mutations.py      → 0 failures
pytest tests/unit/test_chatml_format.py  → 0 failures
pytest tests/integration/test_pipeline.py→ 0 failures
python corpus/scripts/07_validate_corpus.py → exit 0
```

And the corpus statistics meet:
```
datasets/train.jsonl  ≥ 7,000 lines
datasets/eval.jsonl   ≥   800 lines
datasets/test.jsonl   ≥   800 lines
All 70 (atelier × sector) strata present in each split
Zero forbidden terms in Volet 1 + 2 examples
G/V scales present in 100% of A3/A4/A5 Volet 1 + 2 examples
```
