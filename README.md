# LLM EBIOS RM — Assistant IA pour l'analyse de risques ANSSI

> **Un modèle de langage spécialisé dans la méthode EBIOS Risk Manager, déployable 100 % hors ligne (air-gapped), conforme à la terminologie officielle ANSSI 2024.**

[![Licence Apache 2.0](https://img.shields.io/badge/Licence-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Modèle base](https://img.shields.io/badge/Modèle-Mistral_7B_Instruct_v0.3-orange.svg)](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3)
[![Statut](https://img.shields.io/badge/Statut-POC_en_cours-yellow.svg)]()
[![ANSSI EBIOS RM](https://img.shields.io/badge/Méthode-EBIOS_RM_2024-red.svg)](https://www.ssi.gouv.fr/guide/ebios-risk-manager-la-methode/)
[![Qualification ANSSI](https://img.shields.io/badge/Qualification_ANSSI-En_préparation-lightgrey.svg)]()

---

## Présentation

**LLM EBIOS RM** est un assistant IA open source conçu pour accompagner les analystes et consultants en cybersécurité dans la conduite d'analyses de risques numériques selon la méthode [EBIOS Risk Manager](https://www.ssi.gouv.fr/guide/ebios-risk-manager-la-methode/) publiée par l'ANSSI.

Il repose sur **Mistral 7B Instruct v0.3** fine-tuné sur un corpus d'exemples EBIOS RM annotés, enrichi d'un système RAG (Retrieval-Augmented Generation) indexant la documentation officielle ANSSI. L'ensemble du système fonctionne **intégralement hors ligne** — aucune donnée ne quitte l'infrastructure de l'organisation.

```
┌──────────────────────────────────────────────────────┐
│  INTERFACE (LM Studio · FastAPI · Streamlit)         │
├──────────────────────────────────────────────────────┤
│  ORCHESTRATION (LangChain · ChromaDB · Prompts)      │
├──────────────────────────────────────────────────────┤
│  INFÉRENCE (Mistral 7B fine-tuné · llama.cpp)        │
└──────────────────────────────────────────────────────┘
         100 % local — 100 % offline — Apache 2.0
```

---

## Pourquoi ce projet ?

La méthode EBIOS RM est la référence française et européenne pour l'appréciation des risques numériques. Elle est reconnue par l'ANSSI, compatible ISO/IEC 27005:2022, et recommandée pour les démarches d'homologation et de mise en conformité NIS2.

Elle est aussi perçue comme **complexe à mettre en œuvre**, notamment pour :

- les organisations moins matures en cybersécurité qui abordent la méthode pour la première fois ;
- les consultants qui gèrent plusieurs analyses en parallèle et ont besoin d'un appui structurant ;
- les RSSI qui souhaitent documenter leurs analyses de manière rigoureuse sans maîtriser toutes les subtilités des 5 ateliers.

Les solutions LLM génériques (ChatGPT, Copilot…) ne connaissent pas la terminologie officielle ANSSI 2024, confondent régulièrement les échelles de cotation, et ne peuvent pas être utilisées pour des analyses confidentielles. Ce projet répond à ces trois problèmes simultanément.

---

## Fonctionnalités couvertes

L'assistant guide le praticien à travers l'intégralité des 5 ateliers de la méthode :

| Atelier | Contenu | Statut |
|---------|---------|--------|
| **A1 — Cadrage et socle de sécurité** | Missions, valeurs métier, biens supports, événements redoutés, gravité, socle de sécurité | 🟡 En cours |
| **A2 — Sources de risque** | Identification et qualification des couples SR/OV, cartographie des sources de risque | 🟡 En cours |
| **A3 — Scénarios stratégiques** | Écosystème, dangerosité des parties prenantes, chemins d'attaque, mesures sur l'écosystème | 🟡 En cours |
| **A4 — Scénarios opérationnels** | Modes opératoires, actions élémentaires, vraisemblance (méthodes expresse/standard/avancée) | 🟡 En cours |
| **A5 — Traitement du risque** | Plan de traitement du risque, risques résiduels, cartographie initiale/résiduelle | 🟡 En cours |

**Ce que le LLM fait concrètement :**

- Génère les tableaux de valeurs métier et biens supports à partir d'une description de contexte
- Propose des couples Sources de risque / Objectifs visés adaptés au secteur d'activité
- Construit des scénarios stratégiques avec leurs chemins d'attaque
- Calcule automatiquement les niveaux de dangerosité des parties prenantes selon la formule officielle ANSSI
- Propose un plan de traitement du risque structuré avec responsables et échéances
- Vérifie en permanence la conformité terminologique avec la méthode EBIOS RM 2024

---

## Ce que ce projet n'est pas

- **Ce n'est pas un outil de cybersécurité opérationnelle** (SIEM, EDR, scanner de vulnérabilités)
- **Ce n'est pas un substitut à l'expertise humaine** : il assiste le praticien, ne le remplace pas
- **Ce n'est pas encore certifié ou qualifié** : la démarche de qualification ANSSI est en cours
- **Ce n'est pas un service SaaS** : il se déploie exclusivement en local (air-gapped par conception)

---

## Architecture technique

### Couche inférence

| Composant | Rôle | Détail |
|-----------|------|--------|
| **Mistral 7B Instruct v0.3** | Modèle de base | Licence Apache 2.0, français natif, 7.24B paramètres |
| **llama.cpp** | Moteur d'inférence | Exécution CPU/GPU, format GGUF |
| **Ollama** | API REST locale | `http://localhost:11434`, compatible OpenAI |
| **LM Studio** | Interface utilisateur | Chargement du GGUF fine-tuné |
| **GGUF Q4_K_M** | Format livrable | ~4.1 Go, 8 Go RAM suffisants en CPU |

### Couche orchestration

| Composant | Rôle | Détail |
|-----------|------|--------|
| **LangChain 0.3+** | Pipeline LCEL | Chaîne RAG + validation + mémoire |
| **ChromaDB** | Base vectorielle | Persistante, ~1 800 chunks, offline |
| **nomic-embed-text** | Embeddings | 768 dims, multilingue, local via Ollama |
| **BM25** | Retrieval lexical | Retrieval hybride 70% sémantique / 30% lexical |

### Pipeline de fine-tuning

| Étape | Outil | Détail |
|-------|-------|--------|
| **Corpus** | Scripts Python + Claude API | ~10 000 paires instruction/réponse |
| **Fine-tuning** | Unsloth + TRL SFTTrainer | QLoRA r=16 α=32, 3 epochs |
| **Alternative** | LLaMA-Factory | Support multi-GPU (2× RTX 3090) |
| **Export** | llama.cpp convert | GGUF Q4_K_M + Q5_K_M |

### Paramètres LoRA

```python
lora_r            = 16      # Rang
lora_alpha        = 32      # Scaling (α/r = 2.0)
lora_dropout      = 0.05
max_seq_length    = 2048
learning_rate     = 2e-4
num_train_epochs  = 3
per_device_batch  = 4       # A100 40 Go
gradient_accum    = 4       # Effective batch = 16
```

---

## Structure du projet

```
ebios-rm-llm/
├── CLAUDE.md                    # Contexte principal pour agents IA (OpenCode)
├── AGENTS.md                    # Navigation rapide par module
├── Makefile                     # Interface de commandes unifiée
├── pyproject.toml               # Dépendances et configuration
│
├── corpus/                      # Pipeline corpus (10 000 exemples annotés)
│   ├── AGENTS.md
│   ├── scripts/
│   │   ├── 01_extract_pdf.py    # Extraction documentaire ANSSI
│   │   ├── 02_generate_synthetics.py
│   │   ├── 03_generate_counterexamples.py
│   │   ├── 04_quality_filter.py
│   │   ├── 05_format_chatml.py
│   │   ├── 06_stratified_split.py
│   │   ├── 07_validate_corpus.py
│   │   └── schema.py            # ◆ Source de vérité du schéma corpus
│   └── datasets/                # train.jsonl · validation.jsonl · test.jsonl
│
├── finetuning/                  # Pipeline QLoRA + export GGUF
│   ├── AGENTS.md
│   ├── configs/                 # lora_config.yaml · training_args.yaml
│   └── scripts/
│       ├── train_unsloth.py
│       ├── merge_lora.py
│       └── quantize_gguf.py
│
├── evaluation/                  # Benchmark méthodologique EBIOS RM
│   ├── AGENTS.md
│   ├── benchmarks/
│   │   ├── ebios_rules.py       # ◆ Source de vérité des règles EBIOS
│   │   └── atelier_checks.py    # Vérifications spécifiques par atelier
│   ├── scripts/                 # Scoring automatique + génération rapport
│   └── testsets/                # 500 cas de test par atelier (A1→A5)
│
├── rag/                         # Index ChromaDB + pipeline embeddings
│   ├── AGENTS.md
│   └── scripts/                 # build_index.py · test_retrieval.py
│
├── prompts/                     # Templates hiérarchiques par atelier
│   ├── AGENTS.md
│   ├── system/                  # system_prompt.py
│   ├── ateliers/                # A1_cadrage.py → A5_traitement.py
│   └── validation/              # guard_prompt.py
│
├── inference/                   # Configs Ollama + LM Studio
│   ├── AGENTS.md
│   ├── modelfiles/Modelfile.ebios
│   └── configs/                 # lm_studio_config.json · inference_params.yaml
│
├── orchestration/               # LangChain chains + mémoire session
│   ├── AGENTS.md
│   ├── chains/                  # rag_chain.py · validation_chain.py
│   ├── memory/                  # session_memory.py · atelier_context.py
│   └── routers/                 # atelier_router.py · step_router.py
│
├── app/                         # FastAPI + Streamlit (optionnel)
│   ├── AGENTS.md
│   ├── api/                     # routes.py · models.py · dependencies.py
│   └── ui/                      # streamlit_app.py
│
├── compliance/                  # Traçabilité qualification ANSSI
│   ├── AGENTS.md
│   ├── matrices/
│   │   ├── anssi_requirements.py  # ◆ 128 exigences officielles ANSSI
│   │   └── compliance_matrix.py   # Matrice de couverture par module
│   └── scripts/
│       └── run_compliance_check.py
│
└── tests/                       # Unit · Intégration · E2E
    ├── AGENTS.md
    ├── unit/
    ├── integration/
    └── e2e/
```

---

## Démarrage rapide

### Prérequis

- Python 3.10 ou supérieur
- [Ollama](https://ollama.ai) installé et en cours d'exécution
- 8 Go de RAM minimum (16 Go recommandés pour le mode CPU)
- GPU NVIDIA optionnel (RTX 3060+ avec 8 Go VRAM pour de meilleures performances)

### Installation

```bash
# 1. Cloner le dépôt
git clone https://github.com/[votre-username]/ebios-rm-llm.git
cd ebios-rm-llm

# 2. Installer l'environnement
make setup

# 3. Télécharger les modèles Ollama nécessaires
ollama pull nomic-embed-text    # Modèle d'embedding (RAG)
# Le modèle Mistral fine-tuné sera disponible prochainement

# 4. Vérifier que tout fonctionne
make health
```

### Utilisation avec LM Studio (livrable principal)

1. Télécharger [LM Studio](https://lmstudio.ai/) (version 0.3+)
2. Charger le fichier `finetuning/output/mistral-7b-ebios-rm-q4_k_m.gguf` *(disponible prochainement)*
3. Importer la configuration `inference/configs/lm_studio_config.json`
4. Démarrer une conversation avec le prompt d'atelier correspondant à votre besoin

### Utilisation via l'API locale

```bash
# Démarrer l'API FastAPI
make serve

# Exemple de requête — Atelier 1 : génération de valeurs métier
curl -X POST http://localhost:8000/api/atelier/A1 \
  -H "Content-Type: application/json" \
  -d '{
    "organisation": "Hôpital universitaire, 3 000 lits",
    "secteur": "sante",
    "etape": "B",
    "contexte": "SI de gestion des patients (DPI), interconnecté avec les laboratoires et la pharmacie"
  }'
```

---

## Commandes Make disponibles

```bash
# Environnement
make setup              # Installe l'environnement complet (venv + dépendances)
make health             # Vérifie que tous les services sont opérationnels

# Pipeline corpus
make build-corpus       # Exécute les 7 étapes du pipeline corpus
# → Livrable : corpus/datasets/train.jsonl (~9 000 exemples)

# Fine-tuning (GPU requis)
make train              # Lance le fine-tuning QLoRA (Unsloth)
make train-llamafactory # Alternative via LLaMA-Factory
make merge-export       # Fusionne les poids LoRA + exporte GGUF Q4_K_M

# Évaluation
make evaluate           # Benchmark EBIOS RM complet (500 cas/atelier)
# → Livrable : evaluation/reports/validation_methodologique.pdf

# RAG
make build-rag          # Construit l'index ChromaDB depuis les PDFs ANSSI
make test-rag           # Vérifie la qualité du retrieval

# Tests
make test               # Tous les tests (unit + intégration)
make test-unit          # Tests unitaires uniquement (pas de GPU)
make test-e2e           # Tests bout en bout (modèle requis)

# Qualification ANSSI
make compliance-check   # Vérifie la cohérence de la matrice de conformité
make compliance-stats   # Affiche les statistiques de couverture
make compliance-report  # Génère le rapport PDF de conformité

# Application
make serve              # API FastAPI locale (port 8000)
make serve-ui           # Interface Streamlit (port 8501)
```

---

## Terminologie officielle EBIOS RM 2024

Ce projet applique **strictement** la terminologie de la version 2024 du guide ANSSI. Les termes de l'ancienne méthode EBIOS 2010 sont explicitement interdits dans tout le code, les prompts et le corpus.

| ❌ À ne jamais utiliser | ✅ Terme officiel EBIOS RM 2024 |
|------------------------|--------------------------------|
| Biens essentiels | **Valeurs métier** |
| Actifs | **Biens supports** |
| Menaces (seul) | **Sources de risque** + **Objectifs visés** |
| PACS | **Plan de traitement du risque** |
| Biens essentiels / Actifs critiques | **Valeurs métier** ou **Biens supports** |

Les **échelles de cotation officielles** sont également implémentées :

- **Gravité** : G1 (Mineure) · G2 (Significative) · G3 (Grave) · G4 (Critique)
- **Vraisemblance** : V1 (Peu vraisemblable) · V2 (Vraisemblable) · V3 (Très vraisemblable) · V4 (Quasi-certain)
- **Dangerosité PP** : (Dépendance × Pénétration) / (Maturité SSI × Confiance)

---

## Qualification ANSSI

Ce projet vise la qualification des outils EBIOS RM par l'ANSSI. Les 128 exigences officielles du référentiel de qualification sont intégralement tracées dans le module `compliance/`.

### État de conformité actuel

| Statut | Nombre | Description |
|--------|--------|-------------|
| ✅ DONE | 3 | Implémenté et testé |
| 🟡 IN_PROGRESS | 41 | En cours d'implémentation |
| ⬜ TODO | 79 | À implémenter |
| ➖ N/A | 5 | SaaS uniquement (hors scope POC offline) |
| **Total** | **128** | Exigences ANSSI |

31 exigences **P0 (bloquantes)** sont en cours de traitement en priorité.

```bash
# Afficher l'état de conformité en temps réel
make compliance-stats
```

La matrice complète est disponible dans [`compliance/matrices/compliance_matrix.py`](compliance/matrices/compliance_matrix.py).

---

## Données de performance (objectifs POC)

| Métrique | Seuil minimal | Cible |
|----------|--------------|-------|
| Conformité globale EBIOS RM | 75% | **≥ 80%** |
| Terminologie officielle ANSSI | 90% | **≥ 95%** |
| Cohérence inter-ateliers A1→A5 | 80% | **≥ 85%** |
| Hallucinations factuelles | ≤ 10% | **≤ 5%** |
| Couverture des 5 ateliers | 100% | **100%** |

Ces métriques sont mesurées automatiquement via `make evaluate` sur un jeu de 500 cas de test par atelier (holdout, jamais vu pendant l'entraînement).

---

## Ressources matérielles requises

### Inférence (usage quotidien)

| Configuration | RAM | VRAM | Débit |
|---------------|-----|------|-------|
| CPU uniquement (Q4_K_M) | 16 Go | — | ~5 tokens/s |
| GPU RTX 3060 (Q4_K_M) | 16 Go | 8 Go | ~40 tokens/s |
| GPU RTX 3090 (Q5_K_M) | 16 Go | 24 Go | ~60 tokens/s |

### Fine-tuning (phase de développement)

| GPU | VRAM | Durée (3 epochs) | Coût cloud |
|-----|------|-----------------|------------|
| NVIDIA A100 40 Go | ~22 Go | ~4–6 heures | ~16€ |
| 2× RTX 3090 24 Go | ~20 Go/GPU | ~6–8 heures | — |
| Google Colab Pro (A100) | 40 Go | ~5 heures | ~10€/mois |

---

## Contribuer

Les contributions sont bienvenues, en particulier sur les axes suivants :

### Ce dont le projet a besoin en priorité

- **Exemples de corpus validés** : des paires instruction/réponse EBIOS RM sur des cas réels et anonymisés (tout secteur)
- **Beta testeurs praticiens** : des analystes EBIOS RM qui veulent tester les 5 ateliers sur leurs propres contextes
- **Revue terminologique** : vérifier que les prompts et le corpus respectent la terminologie ANSSI 2024
- **Tests d'intégration** : compléter la couverture de tests sur les modules LangChain

### Comment contribuer

```bash
# Fork + clone
git clone https://github.com/[votre-username]/ebios-rm-llm.git
cd ebios-rm-llm

# Créer une branche
git checkout -b feat/ma-contribution

# Installer en mode développement
make setup

# Lancer les tests avant de soumettre
make test-unit
make compliance-check

# Soumettre une Pull Request
```

### Conventions de contribution

1. **Terminologie** : tout texte en français doit utiliser les termes officiels EBIOS RM 2024 (voir tableau ci-dessus). Le script `compliance/scripts/run_compliance_check.py` vérifie automatiquement.
2. **Tests** : tout nouveau module doit s'accompagner de tests unitaires dans `tests/unit/`.
3. **Schema** : tout exemple de corpus doit respecter le schéma défini dans `corpus/scripts/schema.py`.
4. **Format** : `ruff check .` doit passer sans erreur.

---

## Feuille de route

| Horizon | Objectif |
|---------|----------|
| **M1–M5** | Corpus 10 000 exemples + index RAG ChromaDB complet |
| **M5–M8** | Fine-tuning v1 + export GGUF + benchmark initial |
| **M8–M12** | Orchestration LangChain complète + prompts A1-A5 validés |
| **M12–M15** | API FastAPI + conformité ANSSI P0 (31 exigences) |
| **M15–M17** | Beta test avec praticiens EBIOS + validation experte |
| **M18** | Dépôt du dossier de qualification ANSSI |

---

## Références

- [Guide EBIOS Risk Manager — ANSSI (2024)](https://www.ssi.gouv.fr/guide/ebios-risk-manager-la-methode/)
- [Fiches méthodes EBIOS RM — Le Supplément](https://www.ssi.gouv.fr/guide/ebios-risk-manager-la-methode/)
- [Club EBIOS](https://www.club-ebios.org/)
- [Mistral 7B Instruct v0.3 — HuggingFace](https://huggingface.co/mistralai/Mistral-7B-Instruct-v0.3)
- [Référentiel de qualification des outils EBIOS RM — ANSSI](https://www.ssi.gouv.fr/)
- [NIS2 — Transposition française](https://www.ssi.gouv.fr/entreprise/reglementation/cybersecurite-des-operateurs/la-directive-nis/)
- [ISO/IEC 27005:2022 — Gestion des risques liés à la sécurité de l'information](https://www.iso.org/standard/80585.html)

---

## Avertissements

**Ce projet est en phase de Proof of Concept (POC).** Il n'est pas encore qualifié par l'ANSSI. Les sorties du modèle doivent systématiquement être revues par un praticien EBIOS RM compétent avant toute utilisation dans le cadre d'une homologation ou d'une analyse de risques formelle.

L'utilisation de ce logiciel ne se substitue pas à une démarche d'homologation de sécurité ni aux certifications décrites sur le site de l'ANSSI.

---

## Licence

Ce projet est distribué sous licence **Apache 2.0**. Voir le fichier [LICENSE](LICENSE) pour les détails.

Les documents de référence ANSSI (guide EBIOS RM, fiches méthodes) sont distribués sous **Licence Ouverte / Open Licence Etalab v1** et ne sont pas inclus dans ce dépôt. Ils doivent être téléchargés directement depuis le [site de l'ANSSI](https://www.ssi.gouv.fr/).

---

## Contact

Pour toute question sur le projet, les collaborations ou la démarche de qualification ANSSI, ouvrez une [issue GitHub](../../issues) ou contactez-nous via les [Discussions](../../discussions).

Si vous êtes praticien EBIOS RM certifié et souhaitez participer à la validation du modèle, votre contribution est particulièrement précieuse — n'hésitez pas à vous manifester.

---

<div align="center">

**LLM EBIOS RM** · Projet open source · Licence Apache 2.0

*Construire un assistant IA souverain pour l'analyse de risques numériques en France*

</div>
