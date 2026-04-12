# ═══════════════════════════════════════════════════════
# Makefile — LLM EBIOS RM
# Commandes principales du projet
# ═══════════════════════════════════════════════════════

.PHONY: help setup build-corpus train merge-export evaluate build-rag test serve clean

PYTHON = python3
VENV = .venv
PIP = $(VENV)/bin/pip
PY = $(VENV)/bin/python

help: ## Affiche cette aide
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Installe l'environnement complet (venv + dépendances)
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@echo "✓ Environnement prêt. Activer avec : source $(VENV)/bin/activate"
	@echo "→ Vérifiez que Ollama tourne : ollama serve"
	@echo "→ Téléchargez nomic-embed-text : ollama pull nomic-embed-text"

# ── Pipeline corpus (Étapes 1-2) ────────────────────────
build-corpus: ## [Étapes 1-2] Construit le corpus d'entraînement complet
	$(PY) corpus/scripts/01_extract_pdf.py
	$(PY) corpus/scripts/02_generate_synthetics.py
	$(PY) corpus/scripts/03_generate_counterexamples.py
	$(PY) corpus/scripts/04_quality_filter.py
	$(PY) corpus/scripts/05_format_chatml.py
	$(PY) corpus/scripts/06_stratified_split.py
	$(PY) corpus/scripts/07_validate_corpus.py
	@echo "✓ Corpus construit → corpus/datasets/"

# ── Fine-tuning (Étape 3) ────────────────────────────────
train: ## [Étape 3] Lance le fine-tuning LoRA/QLoRA (GPU requis)
	@echo "⚠ Vérification corpus..."
	@test -f corpus/datasets/train.jsonl || (echo "❌ Corpus manquant. Lancez 'make build-corpus'" && exit 1)
	@echo "🚀 Lancement fine-tuning Unsloth..."
	$(PY) finetuning/scripts/train_unsloth.py
	@echo "✓ Training terminé → finetuning/checkpoints/"

train-llamafactory: ## [Étape 3] Alternative : fine-tuning via LLaMA-Factory
	$(PY) finetuning/scripts/train_llamafactory.py

# ── Merge + Export GGUF (Étape 4) ───────────────────────
merge-export: ## [Étape 4] Fusionne LoRA + exporte GGUF Q4_K_M et Q5_K_M
	$(PY) finetuning/scripts/merge_lora.py
	$(PY) finetuning/scripts/quantize_gguf.py
	$(PY) finetuning/scripts/verify_model.py
	@echo "✓ Modèle exporté → finetuning/output/"

# ── Évaluation (Étape 5) ─────────────────────────────────
evaluate: ## [Étape 5] Lance le benchmark EBIOS RM complet
	@test -f finetuning/output/mistral-7b-ebios-rm-q4_k_m.gguf || \
		(echo "❌ Modèle GGUF manquant. Lancez 'make merge-export'" && exit 1)
	$(PY) evaluation/scripts/run_benchmark.py
	$(PY) evaluation/scripts/generate_report.py
	@echo "✓ Rapport d'évaluation → evaluation/reports/"

# ── RAG (Base vectorielle) ───────────────────────────────
build-rag: ## Construit l'index ChromaDB depuis les documents EBIOS
	@echo "⚠ OPENROUTER_API_KEY doit être définie dans .env"
	@echo "  Modèle: intfloat/multilingual-e5-base (768 dims)"
	@echo "  Sources: PDF ANSSI + CSV MITRE + corpus synthétique"
	$(PY) rag/scripts/build_index.py --reset --all-sources
	@echo "✓ Index RAG construit → data/chroma_db/"

test-rag: ## Teste la qualité du retrieval ChromaDB
	$(PY) rag/scripts/test_retrieval.py

# ── Tests ────────────────────────────────────────────────
test: test-unit test-integration ## Lance tests unit + intégration
	@echo "✓ Tests terminés"

test-unit: ## Tests unitaires (pas de GPU requis)
	$(VENV)/bin/pytest tests/unit/ -v --tb=short

test-integration: ## Tests intégration (Ollama doit tourner)
	$(VENV)/bin/pytest tests/integration/ -v --tb=short

test-e2e: ## Tests bout en bout (modèle GGUF chargé requis)
	$(VENV)/bin/pytest tests/e2e/ -v --tb=short -s

# ── Application ──────────────────────────────────────────
serve: ## Démarre l'API FastAPI locale (port 8000)
	$(VENV)/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

serve-ui: ## Démarre l'interface Streamlit (port 8501)
	$(VENV)/bin/streamlit run app/ui/streamlit_app.py

# ── Livrables ────────────────────────────────────────────
export-deliverables: ## Package les livrables L2-L6 pour livraison
	bash scripts/export_deliverables.sh

# ── Utilitaires ──────────────────────────────────────────
health: ## Vérifie que tous les services sont opérationnels
	bash scripts/check_health.sh

clean: ## Nettoie les fichiers temporaires
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
	@echo "✓ Nettoyage terminé"

# ── Qualification ANSSI ──────────────────────────────
compliance-check: ## Vérifie la cohérence de la matrice de conformité ANSSI
	$(PY) compliance/scripts/run_compliance_check.py
	@echo "✓ Vérification conformité terminée"

compliance-report: ## Génère le rapport PDF de conformité ANSSI (livrable qualification)
	$(PY) compliance/scripts/generate_conformity_report.py
	@echo "✓ Rapport de conformité → compliance/docs/rapport_conformite_anssi.pdf"

compliance-stats: ## Affiche les statistiques de couverture des exigences ANSSI
	$(PY) compliance/matrices/compliance_matrix.py
