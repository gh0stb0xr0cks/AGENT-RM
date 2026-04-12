# AGENTS.md — corpus/

## Rôle de ce module

Construire le dataset d'entraînement EBIOS RM : 10 000 paires instruction/réponse
couvrant les 5 ateliers, dans ≥6 secteurs, validées par un expert certifié.

## Pipeline d'exécution (ordre obligatoire)

```
scripts/01_extract_pdf.py       → raw/anssi/ + raw/mitre/
scripts/02_generate_synthetics.py → raw/synthetics/
scripts/03_generate_counterexamples.py → raw/synthetics/counterexamples/
scripts/04_quality_filter.py    → processed/filtered.jsonl
scripts/05_format_chatml.py     → processed/chatml.jsonl
scripts/06_stratified_split.py  → datasets/{train,val,test}.jsonl
scripts/07_validate_corpus.py   → validation/report.json
```

Commande globale : `make build-corpus`

## Format de donnée attendu (schema.py)

```python
{
  "messages": [
    {"role": "system",    "content": SYSTEM_PROMPT},
    {"role": "user",      "content": "<contexte>\n<question atelier>"},
    {"role": "assistant", "content": "<réponse EBIOS RM structurée>"}
  ],
  "metadata": {
    "atelier":    "A1"|"A2"|"A3"|"A4"|"A5",
    "etape":      "A"|"B"|"C"|"D",
    "secteur":    "sante"|"industrie"|"collectivite"|"defense"|"finance"|"energie",
    "type":       "guide"|"synthetique"|"contre_exemple",
    "valide_par": "expert_ebios_cert",
    "qualite":    1..5          # ≥4 requis pour inclusion en train
  }
}
```

## Cibles volumétriques

| Volet | Type | Quantité | Ateliers |
|-------|------|----------|---------|
| 1 | Docs officiels ANSSI → Q/R | ~1 500 | A1-A5 |
| 2 | Synthétiques multi-secteurs | ~7 000 | A1-A5 |
| 3 | Contre-exemples + corrections | ~1 500 | A1-A5 |

Split : Train 90% · Validation 5% · Test 5% (stratifié par atelier)

## Filtres qualité automatiques (04_quality_filter.py)

- Longueur tokens : 64 ≤ len ≤ 2048 (tokenizer Mistral)
- Score qualité métadonnées ≥ 4/5
- Aucun terme EBIOS 2010 obsolète dans l'assistant turn
- Format ChatML valide (3 messages minimum)
- Déduplication SHA256 sur le turn assistant

## Termes INTERDITS dans le corpus (tour "assistant")

```python
FORBIDDEN = [
    "biens essentiels", "actifs critiques", "menaces principales",
    "PACS", "plan d'amélioration continue", "risques cyber"
]
```

## Termes REQUIS dans le corpus (au moins 2 sur 4)

```python
REQUIRED = [
    "valeurs métier", "biens supports",
    "événements redoutés", "sources de risque"
]
```

## Secteurs obligatoires (≥100 exemples chacun)

sante · industrie · collectivite · defense · finance · energie

## Fichiers de sortie (datasets/)

- `train.jsonl`      : ~9 000 exemples (entraînement)
- `validation.jsonl` : ~500 exemples (monitoring training)
- `test.jsonl`       : ~500 exemples (évaluation finale, NE PAS UTILISER pendant training)
- `corpus_stats.json`: statistiques complètes du corpus
