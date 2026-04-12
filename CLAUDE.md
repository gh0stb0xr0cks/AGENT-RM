# LLM EBIOS RM — Contexte agent

## Mission
Fine-tuner Mistral 7B Instruct v0.3 comme expert EBIOS RM ANSSI, déployable air-gapped
sous LM Studio. Couvre les 5 ateliers EBIOS RM version 2024.

## Architecture
```
app/          → FastAPI + Streamlit
orchestration/ → LangChain LCEL + ChromaDB RAG
inference/    → Mistral 7B fine-tuné · llama.cpp · Ollama
```

## Commandes clés
```bash
make setup            # Installe l'environnement
make build-corpus     # Pipeline corpus (étapes 1-7)
make train            # Fine-tuning QLoRA (GPU requis)
make merge-export     # Fusionne LoRA + exporte GGUF
make evaluate         # Benchmark EBIOS RM
make build-rag        # Index ChromaDB
make compliance-stats # État qualification ANSSI
make test && make serve
```

## Terminologie EBIOS RM — INTERDITS ABSOLUS
Ces termes appartiennent à EBIOS 2010 (obsolète). Les employer est une erreur bloquante.

| ❌ Interdit | ✅ Correct |
|------------|-----------|
| biens essentiels | valeurs métier |
| actifs | biens supports |
| menaces (seul) | sources de risque + objectifs visés |
| PACS | plan de traitement du risque |

Vérification : `python evaluation/benchmarks/ebios_rules.py`

## Sources de vérité — lire en priorité
- `corpus/scripts/schema.py` → schéma corpus + termes requis/interdits
- `evaluation/benchmarks/ebios_rules.py` → règles scoring EBIOS RM
- `compliance/matrices/anssi_requirements.py` → 128 exigences ANSSI officielles

## Règles non négociables
1. Aucun appel réseau en production (mode offline strict)
2. Tout nouveau module → tests unitaires dans `tests/unit/`
3. Tout exemple corpus → respecter `corpus/scripts/schema.py`
4. Avant commit → `make compliance-check` doit passer
