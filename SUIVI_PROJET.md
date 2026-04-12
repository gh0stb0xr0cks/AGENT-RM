# SUIVI PROJET -- LLM EBIOS RM
> Derniere mise a jour : 31 mars 2026
> Contexte : developpeur solo + assistance IA

---

## 1. ETAT D'AVANCEMENT PAR MODULE

| Module | Fichiers | Implemente | Vide | Lignes | Completion |
|--------|----------|------------|------|--------|------------|
| rag/ | 9 | 9 | 0 | 1 765 | **100%** |
| compliance/ | 4 | 3 | 1 | 1 208 | **75%** |
| orchestration/ | 10 | 5 | 5 | 673 | **50%** |
| evaluation/ | 7 | 2 | 5 | 226 | **29%** |
| tests/ | 10 | 3 | 7 | 897 | **30%** |
| corpus/ | 8 | 1 | 7 | 96 | **12%** |
| prompts/ | 11 | 0 | 11 | 0 | **0%** |
| inference/ | 7 | 0 | 7 | 0 | **0%** |
| finetuning/ | 9 | 0 | 9 | 0 | **0%** |
| app/ | 6 | 0 | 6 | 0 | **0%** |
| scripts/ | 5 | 0 | 5 | 0 | **0%** |
| docs/ | 6 | 0 | 6 | 0 | **0%** |
| **TOTAL** | **102** | **23** | **79** | **4 865** | **~25%** |

---

## 2. ESTIMATION DU TRAVAIL RESTANT (dev solo + IA)

Le facteur de reduction IA est estime a 0.5x-0.6x sur le code Python pur
(prompts, scripts, tests, API) et 0.8x sur le travail experimentale
(fine-tuning, qualite corpus) ou l'IA assiste mais ne remplace pas le jugement.

### LOT 1 -- Prompts & Inference configs (BLOQUEUR CRITIQUE)
Debloque toute la chaine orchestration -> LLM.

| Tache | Estimation |
|-------|-----------|
| system_prompt.py (prompt systeme expert EBIOS) | 1j |
| A1_cadrage.py | 1j |
| A2_sources.py | 1j |
| A3_strategique.py | 1.5j |
| A4_operationnel.py (MITRE ATT&CK) | 1.5j |
| A5_traitement.py | 1j |
| guard_prompt.py + checklist.py | 0.5j |
| ollama_config.py + Modelfile + lm_studio_config | 0.5j |
| **Sous-total** | **8j** |

### LOT 2 -- Pipeline Corpus (~10 000 exemples)
Prerequis au fine-tuning. Le plus consommateur en temps.

| Tache | Estimation |
|-------|-----------|
| 01_extract_pdf.py | 1j |
| 02_generate_synthetics.py (generation via API LLM) | 3j |
| 03_generate_counterexamples.py | 1.5j |
| 04_quality_filter.py | 1j |
| 05_format_chatml.py | 0.5j |
| 06_stratified_split.py | 0.5j |
| 07_validate_corpus.py | 1j |
| Iterations qualite (revue, correction, re-generation) | 3j |
| **Sous-total** | **11.5j** |

### LOT 3 -- Fine-tuning Mistral 7B
Experimentation GPU. L'IA assiste le code mais pas les runs.

| Tache | Estimation |
|-------|-----------|
| train_unsloth.py + configs YAML | 1.5j |
| train_llamafactory.py (alternative) | 1j |
| merge_lora.py | 0.5j |
| quantize_gguf.py (Q4_K_M + Q5_K_M) | 0.5j |
| verify_model.py | 0.5j |
| Experimentation hyperparametres (3-5 runs GPU) | 4j |
| Iterations qualite modele | 3j |
| **Sous-total** | **11.5j** |

### LOT 4 -- Orchestration complete
La base existe (rag_chain.py, memory). Reste les routers et la validation.

| Tache | Estimation |
|-------|-----------|
| atelier_chain.py (chain complete par atelier) | 1j |
| validation_chain.py (guard post-generation) | 1.5j |
| atelier_router.py | 0.5j |
| step_router.py | 0.5j |
| **Sous-total** | **3.5j** |

### LOT 5 -- Evaluation & Benchmark
Le scoring existe (ebios_rules.py). Reste les scripts d'orchestration.

| Tache | Estimation |
|-------|-----------|
| run_benchmark.py | 1j |
| score_terminology.py + score_structure.py | 1j |
| score_coherence.py | 1j |
| generate_report.py (rapport PDF) | 1j |
| Creation testset de reference (50-100 cas) | 2j |
| **Sous-total** | **6j** |

### LOT 6 -- Application (API FastAPI + UI Streamlit)

| Tache | Estimation |
|-------|-----------|
| main.py + config FastAPI | 0.5j |
| api/models.py (schemas Pydantic) | 1j |
| api/routes.py (CRUD tous ateliers) | 3j |
| api/dependencies.py (auth, sessions, securite) | 1.5j |
| ui/streamlit_app.py | 3j |
| ui/components.py (radar, matrice risque) | 2j |
| **Sous-total** | **11j** |

### LOT 7 -- Tests, Compliance & Documentation

| Tache | Estimation |
|-------|-----------|
| Tests unitaires restants (5 fichiers) | 2.5j |
| Tests integration restants (2 fichiers) | 1.5j |
| Tests e2e (2 fichiers) | 2j |
| Tests compliance ANSSI (par categorie EXI) | 3j |
| generate_conformity_report.py | 1j |
| Scripts utilitaires (health, export, download) | 1j |
| Documentation technique (6 fichiers) | 2j |
| **Sous-total** | **13j** |

### RECAPITULATIF TEMPS

| Lot | Jours | % total |
|-----|-------|---------|
| LOT 1 - Prompts & Inference | 8j | 12% |
| LOT 2 - Pipeline Corpus | 11.5j | 17% |
| LOT 3 - Fine-tuning | 11.5j | 17% |
| LOT 4 - Orchestration | 3.5j | 5% |
| LOT 5 - Evaluation | 6j | 9% |
| LOT 6 - Application | 11j | 16% |
| LOT 7 - Tests & Compliance | 13j | 19% |
| **Sous-total brut** | **65j** | |
| Marge imprevu (+15%) | 10j | |
| **TOTAL ESTIME** | **~75 jours ouvrés** | |

A temps plein : **~3.5 mois** (15-16 semaines).
A mi-temps : **~7 mois**.

---

## 3. ESTIMATION COUTS INFRASTRUCTURE (hors RH)

### 3.1 GPU -- Fine-tuning

| Ressource | Specs requises | Usage estime | Options | Cout |
|-----------|---------------|-------------|---------|------|
| Fine-tuning Mistral 7B QLoRA | GPU 24 Go+ VRAM | ~50h (5 runs x 10h) | RTX 4090 local | 0 EUR |
| | | | A100 40Go cloud (RunPod/Lambda) | ~75-100 EUR |
| | | | Google Colab Pro+ | ~50 EUR/mois x 2 = 100 EUR |
| Generation corpus synthetique | GPU ou API | ~30h generation | Via Ollama local (Mistral 7B) | 0 EUR |
| | | | Via API OpenRouter/Together | ~30-50 EUR |

**Scenario GPU local (RTX 4090/A6000) : 0 EUR**
**Scenario full cloud : 100-200 EUR**

### 3.2 API Embeddings

| Service | Usage | Cout unitaire | Cout total |
|---------|-------|--------------|------------|
| OpenRouter (intfloat/multilingual-e5-base) | ~5M tokens (indexation complete + iterations) | ~0.002 EUR/1K tokens | ~10 EUR |
| OpenRouter (generation corpus si API) | ~20M tokens | ~0.50 EUR/1M tokens | ~10 EUR |

**Sous-total API : ~10-20 EUR**

### 3.3 Modeles a telecharger

| Modele | Taille | Cout |
|--------|--------|------|
| Mistral-7B-Instruct-v0.3 (base FT) | ~14 Go (FP16) | Gratuit (HuggingFace) |
| nomic-embed-text (Ollama, backup local) | ~275 Mo | Gratuit (Ollama pull) |
| GGUF exporte (Q4_K_M) | ~4.5 Go | Produit localement |
| GGUF exporte (Q5_K_M) | ~5.5 Go | Produit localement |

**Sous-total modeles : 0 EUR** (tous open-source Apache 2.0 / MIT)

### 3.4 Stockage & Outils

| Poste | Estimation |
|-------|-----------|
| Stockage disque supplementaire (~50 Go modeles + data) | 0 EUR (local) |
| ChromaDB (base vectorielle ~350 Mo cible) | 0 EUR (local) |
| GitHub (repo prive si necessaire) | 0 EUR (gratuit) |
| LM Studio (interface inference) | 0 EUR (gratuit) |
| Ollama (serving local) | 0 EUR (gratuit) |

**Sous-total outils : 0 EUR**

### 3.5 COUT TOTAL INFRASTRUCTURE

| Scenario | Description | Cout total |
|----------|-------------|-----------|
| **Optimal (GPU local)** | RTX 4090 ou equivalent deja disponible, Ollama local pour corpus | **10-20 EUR** |
| **Intermediaire** | Colab Pro+ pour FT, Ollama local pour le reste | **110-150 EUR** |
| **Full cloud** | Location GPU cloud + APIs pour tout | **200-300 EUR** |

---

## 4. CHEMIN CRITIQUE (ordre de dependance)

```
Semaine 1-2  : LOT 1 (prompts + inference)
               -> Debloque l'orchestration chain
               
Semaine 2-3  : LOT 4 (orchestration)
               -> Pipeline RAG->prompts->LLM fonctionnel de bout en bout
               
Semaine 3-6  : LOT 2 (corpus)
               -> 10 000 exemples d'entrainement generes et valides
               
Semaine 6-9  : LOT 3 (fine-tuning)
               -> Modele GGUF exporte et verifie
               
Semaine 8-10 : LOT 5 (evaluation) [parallelisable avec fin LOT 3]
               -> Score >= 80% sur benchmark EBIOS
               
Semaine 9-13 : LOT 6 (application) [parallelisable avec LOT 5]
               -> API + UI fonctionnels
               
Semaine 13-16: LOT 7 (tests + compliance + docs)
               -> Couverture tests >= 80%, matrice conformite ANSSI
```

**Goulot d'etranglement : LOT 2 + LOT 3** (corpus + fine-tuning).
C'est la ou le temps reel depasse le temps de dev pur : les runs GPU prennent
des heures et la qualite du corpus necessite des iterations manuelles.

---

## 5. RISQUES IDENTIFIES

| Risque | Impact | Probabilite | Mitigation |
|--------|--------|-------------|------------|
| Qualite corpus insuffisante -> modele mediocre | Tres haut | Moyenne | Filtrage strict + contre-exemples + evaluation iterative |
| VRAM insuffisante pour Mistral 7B QLoRA | Haut | Faible si 24Go+ | Reduire batch_size, utiliser gradient checkpointing |
| Score benchmark < 80% apres 3 runs | Haut | Moyenne | Augmenter corpus, ajuster prompts, LoRA rank |
| Embedding model change d'API/prix | Faible | Faible | Fallback nomic-embed-text local via Ollama |
| Qualification ANSSI exige plus que le POC | Moyen | Haute | Documenter les limites POC dans le dossier |

---

## 6. LIVRABLES ET JALON POC (12 semaines)

| Ref | Livrable | Dependance | Statut |
|-----|----------|------------|--------|
| L2 | corpus/datasets/ebios_rm_corpus.jsonl (~10K exemples) | LOT 2 | TODO |
| L3 | Pipeline fine-tuning documente | LOT 3 | TODO |
| L4 | mistral-7b-ebios-rm-q4_k_m.gguf | LOT 3 | TODO |
| L5 | Configs LM Studio + prompts ateliers | LOT 1 | TODO |
| L6 | Rapport de validation methodologique | LOT 5 | TODO |

---

## 7. SUIVI DES SESSIONS DE DEVELOPPEMENT

| Date | Session | Travail effectue | Duree |
|------|---------|-----------------|-------|
| 2026-03-31 | #1 | Module RAG complet : embedding_config aligne AGENTS.md, OpenRouterEmbeddings partage, chunker token-aware, build_index (PDF+CSV+JSONL), add_documents, test_retrieval, formatting.py, AtelierContext, session_memory, chunk_formatter, 69 tests (unit+integration), compliance matrix MAJ, Makefile corrige | ~3h |
| | | | |

---

*Ce fichier est la source de verite pour le suivi du projet.
Le mettre a jour a chaque session de developpement.*
