# AGENTS.md — tests/

## Rôle de ce module

Tests automatisés couvrant les 3 niveaux : unitaires, intégration, e2e.
Chaque module principal doit avoir une couverture ≥80%.

## Structure des tests

```
unit/
  test_corpus_quality.py   → Filtres qualité corpus (termes EBIOS, longueur)
  test_prompts.py          → Rendu des templates d'ateliers (variables, longueur)
  test_scoring.py          → Fonctions de scoring EBIOS RM
  test_formatting.py       → Formatage chunks RAG et sorties

integration/
  test_rag_chain.py        → Retrieval ChromaDB + assemblage prompt
  test_inference.py        → Appel Ollama + génération (modèle chargé requis)
  test_validation_guard.py → Guard post-génération + détection erreurs

e2e/
  test_atelier_flow.py     → Flux complet d'un atelier (A1→A5 séquentiel)
  test_full_ebios_session.py → Session complète 5 ateliers (test de bout en bout)
```

## Fixtures partagées (conftest.py)

```python
# Exemples EBIOS corrects et incorrects pour les tests unitaires
CORRECT_EBIOS_RESPONSE = "..."   # Réponse A1 bien formée
INCORRECT_EBIOS_RESPONSE = "..." # Avec termes EBIOS 2010 interdits

# Client LLM mocké pour tests sans GPU
mock_llm = MockChatOllama(responses=[CORRECT_EBIOS_RESPONSE])
```

## Commandes

```bash
make test             # Tous les tests (unit + integration)
make test-unit        # Tests unitaires uniquement (pas de GPU requis)
make test-integration # Tests intégration (Ollama doit tourner)
make test-e2e         # Tests bout en bout (modèle GGUF chargé requis)
pytest tests/ -v --tb=short  # Détail des erreurs
```

## Tests prioritaires (P0 — blocants pour livraison)

- `test_corpus_quality.py::test_no_forbidden_terms` : aucun terme EBIOS 2010 dans corpus
- `test_prompts.py::test_all_vars_present` : tous les templates compilent sans KeyError
- `test_scoring.py::test_ebios_global_score_above_threshold` : score ≥ 80% sur testset
- `test_validation_guard.py::test_detects_forbidden_terminology` : guard catch les erreurs
