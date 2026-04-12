---
paths:
  - "tests/**/*"
---

# Standards de tests — LLM EBIOS RM

## Tests P0 — bloquants pour toute livraison
Ces tests doivent TOUJOURS passer :
- `test_corpus_quality.py::test_no_forbidden_terms`
- `test_prompts.py::test_all_vars_present`
- `test_scoring.py::test_ebios_global_score_above_threshold`
- `test_validation_guard.py::test_detects_forbidden_terminology`

## Convention de nommage
```
tests/unit/          → test_<module>.py (pas de GPU requis)
tests/integration/   → test_<feature>.py (Ollama doit tourner)
tests/e2e/           → test_<flow>.py    (modèle GGUF requis)
```

## Fixtures partagées (conftest.py)
```python
CORRECT_EBIOS_RESPONSE   # Réponse A1 bien formée — terminologie correcte
INCORRECT_EBIOS_RESPONSE # Contient des termes EBIOS 2010 interdits
mock_llm = MockChatOllama(responses=[CORRECT_EBIOS_RESPONSE])
```

## Règle : tout nouveau module = tests unitaires
Chaque fichier Python créé dans orchestration/, rag/, prompts/ ou compliance/
doit avoir un fichier de test correspondant dans tests/unit/.

## Commandes
```bash
make test-unit        # Rapide, sans GPU
make test-integration # Requiert Ollama actif
make test-e2e         # Requiert modèle GGUF chargé
pytest tests/ -v --tb=short -k "not e2e"  # Unitaires + intégration
```
