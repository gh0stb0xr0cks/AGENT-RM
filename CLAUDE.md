# CLAUDE.md — LLM EBIOS RM · Agent Context Root

## Mission du projet

Fine-tuner Mistral 7B Instruct v0.3 pour en faire un expert EBIOS Risk Manager
certifié ANSSI, déployable intégralement hors ligne (air-gapped) sous LM Studio.
Ce projet couvre les 5 ateliers de la méthode EBIOS RM (version ANSSI 2024).

## Architecture en 3 couches

```
┌─────────────────────────────────────────┐
│  COUCHE INTERFACE (app/)                │
│  LM Studio · Streamlit · FastAPI        │
├─────────────────────────────────────────┤
│  COUCHE ORCHESTRATION (orchestration/)  │
│  LangChain · ChromaDB RAG · Prompts     │
├─────────────────────────────────────────┤
│  COUCHE INFÉRENCE (inference/)          │
│  Mistral 7B Fine-tuné · llama.cpp       │
└─────────────────────────────────────────┘
```

## Conventions absolues — TOUJOURS RESPECTER

### Terminologie EBIOS RM (critique)
L'agent ne doit JAMAIS utiliser les termes suivants dans le code, les prompts
ou les exemples du corpus — ils appartiennent à EBIOS 2010 (obsolète) :
- ❌ "biens essentiels" → ✅ "valeurs métier"
- ❌ "actifs" → ✅ "biens supports" ou "valeurs métier"
- ❌ "menaces" (seul) → ✅ "sources de risque" + "objectifs visés"
- ❌ "PACS" → ✅ "plan de traitement du risque"
- ❌ "risques cyber" → ✅ "scénarios de risque"

Référence officielle : docs/ebios/guide_ebios_rm_2024.pdf

### Échelles de cotation EBIOS RM
- Gravité : G1 (Mineure) · G2 (Significative) · G3 (Grave) · G4 (Critique)
- Vraisemblance : V1 (Peu vraisemblable) · V2 (Vraisemblable) · V3 (Très vraisemblable) · V4 (Quasi-certain)
- Dangerosité PP : formule (Dépendance × Pénétration) / (Maturité × Confiance)

## Stack technique (tout offline, Apache 2.0)

| Rôle | Outil | Version |
|------|-------|---------|
| Modèle base | Mistral 7B Instruct v0.3 | mistralai/Mistral-7B-Instruct-v0.3 |
| Fine-tuning | Unsloth + TRL SFTTrainer | unsloth>=0.3.0, trl>=0.8.0 |
| Alternative FT | LLaMA-Factory | llamafactory>=0.8.0 |
| Inférence | llama.cpp + Ollama | llama-cpp-python>=0.2.0 |
| Interface | LM Studio | >=0.3.0 (GGUF Q4_K_M) |
| Orchestration | LangChain | langchain>=0.3.0 |
| Vector DB | ChromaDB | chromadb>=0.5.0 |
| Embeddings | nomic-embed-text | via Ollama |
| Format livrable | GGUF Q4_K_M / Q5_K_M | llama.cpp convert |

## Structure des modules

```
corpus/          → Pipeline corpus : collecte, synthèse, validation (AGENTS.md)
finetuning/      → LoRA/QLoRA training + merge + quantification (AGENTS.md)
evaluation/      → Benchmark méthodologique EBIOS RM (AGENTS.md)
rag/             → ChromaDB index + embedding pipeline (AGENTS.md)
prompts/         → Templates hiérarchiques par atelier A1→A5 (AGENTS.md)
inference/       → Modelfile Ollama + configs LM Studio (AGENTS.md)
orchestration/   → LangChain chains + mémoire session (AGENTS.md)
app/             → FastAPI + Streamlit interface optionnelle (AGENTS.md)
tests/           → Unit + integration + e2e (AGENTS.md)
```

## Commandes principales (voir Makefile)

```bash
make setup          # Installe l'environnement complet
make build-corpus   # Exécute le pipeline corpus (étapes 1-2)
make train          # Lance le fine-tuning (étape 3, GPU requis)
make merge-export   # Fusionne LoRA + exporte GGUF (étape 4)
make evaluate       # Lance le benchmark EBIOS RM (étape 5)
make build-rag      # Construit l'index ChromaDB
make test           # Lance tous les tests
make serve          # Démarre l'API locale (port 8000)
```

## Paramètres LoRA (NE PAS MODIFIER sans justification)

```python
LORA_R = 16          # Rang — compromis capacité/efficacité
LORA_ALPHA = 32      # Scaling = alpha/r = 2.0
LORA_DROPOUT = 0.05  # Régularisation légère
MAX_SEQ_LENGTH = 2048
LEARNING_RATE = 2e-4
NUM_EPOCHS = 3
BATCH_SIZE = 4       # Per device (A100 40Go)
GRAD_ACCUM = 4       # Effective batch = 16
```

## Livrables du POC (12 semaines)

- **L2** : `corpus/datasets/ebios_rm_corpus.jsonl` (~10 000 exemples validés)
- **L3** : `finetuning/` + `docs/architecture/pipeline_finetuning.md`
- **L4** : `finetuning/output/mistral-7b-ebios-rm-q4_k_m.gguf`
- **L5** : `inference/configs/lm_studio_config.json` + `prompts/`
- **L6** : `evaluation/reports/validation_methodologique.pdf`

## Règles de développement

1. **Mode offline strict** : aucun appel réseau en production (hors phase FT cloud)
2. **Tests obligatoires** : tout nouveau module doit avoir ses tests unitaires
3. **Validation terminologique** : utiliser `evaluation/benchmarks/ebios_rules.py`
   pour vérifier qu'aucun terme EBIOS 2010 n'est introduit
4. **Format corpus** : toujours utiliser le schéma `corpus/scripts/schema.py`
5. **Checkpoints** : sauvegarder toutes les 100 steps pendant le training

## Contacts et références

- Méthode : `docs/ebios/guide_ebios_rm_2024.pdf` (source de vérité)
- Fiches méthode : `docs/ebios/fiches_methodes.pdf`
- Matrice rapport : `docs/ebios/matrice_rapport_sortie.pdf`
- Proposition technique : `docs/specs/proposition_technique.md`

## Qualification ANSSI — Module compliance/

Le projet vise la qualification ANSSI des outils EBIOS RM.
128 exigences officielles sont tracées dans :
- `compliance/matrices/anssi_requirements.py` → libellés officiels (SOURCE DE VÉRITÉ)
- `compliance/matrices/compliance_matrix.py`  → couverture par module (MATRICE DE SUIVI)

### Deux dimensions de conformité à distinguer

1. **Conformité LLM (M1-M5)** : le LLM génère des sorties méthodologiquement correctes
   → Mesurée par `evaluation/benchmarks/ebios_rules.py`

2. **Conformité applicative (M1-M5 + S1-S6)** : l'application gère les données EBIOS
   → Mesurée par `compliance/tests/` + audit ANSSI

### Exigences P0 (bloquantes qualification) — priorité absolue

Toutes les exigences marquées `priority="P0"` dans `compliance_matrix.py` doivent
atteindre le statut `DONE` avant tout dépôt de dossier de qualification ANSSI.

### Commandes qualification

```bash
make compliance-check   # Vérifie cohérence de la matrice
make compliance-report  # Génère le rapport de conformité
python compliance/matrices/compliance_matrix.py  # Stats rapides
```

### Exigences SaaS (EXI_SNC*)

Les 5 exigences SNC (SecNumCloud) sont marquées N/A pour le POC
qui cible un déploiement exclusivement local (air-gapped).
Elles s'appliquent uniquement en cas de déploiement SaaS futur.
