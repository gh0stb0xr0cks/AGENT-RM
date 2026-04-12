---
paths:
  - "corpus/**/*"
---

# Règles corpus EBIOS RM

## Schéma obligatoire — importer depuis schema.py
```python
from corpus.scripts.schema import CorpusExample, CorpusMetadata, Atelier, Secteur
```
Tout exemple qui ne respecte pas ce schéma est refusé par le filtre qualité.

## Format ChatML attendu
```json
{
  "messages": [
    {"role": "system",    "content": "<SYSTEM_PROMPT>"},
    {"role": "user",      "content": "<contexte_organisation>\n<question_atelier>"},
    {"role": "assistant", "content": "<réponse_EBIOS_structurée>"}
  ],
  "metadata": {
    "atelier": "A1|A2|A3|A4|A5",
    "etape":   "A|B|C|D",
    "secteur": "sante|industrie|collectivite|defense|finance|energie",
    "type":    "guide|synthetique|contre_exemple",
    "qualite": 4
  }
}
```

## Ordre d'exécution des scripts (ne pas sauter d'étape)
01 → 02 → 03 → 04 → 05 → 06 → 07
`make build-corpus` exécute la séquence complète.

## Split cible
- train.jsonl      : 90 % (~9 000 ex.)
- validation.jsonl : 5 %  (~500 ex.)
- test.jsonl       : 5 %  (~500 ex.) — NE JAMAIS charger pendant le training

## Filtres qualité obligatoires (04_quality_filter.py)
- Longueur : 64 ≤ tokens ≤ 2048
- Score métadonnées ≥ 4/5
- Aucun terme EBIOS 2010 dans le turn "assistant"
- Format ChatML valide (3 messages min.)
- Déduplication SHA256

## Volumétrie secteurs (≥ 100 exemples chacun)
sante · industrie · collectivite · defense · finance · energie
