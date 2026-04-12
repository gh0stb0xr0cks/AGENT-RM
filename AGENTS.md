# AGENTS.md — Racine du projet LLM EBIOS RM

## Pour l'agent IA : lire CLAUDE.md en premier

CLAUDE.md contient le contexte complet du projet, les conventions de code,
la terminologie EBIOS RM obligatoire, et l'architecture technique.

## Navigation rapide par tâche

| Tâche | Module | AGENTS.md local |
|-------|--------|----------------|
| Générer des exemples de corpus | `corpus/` | `corpus/AGENTS.md` |
| Modifier les scripts de training | `finetuning/` | `finetuning/AGENTS.md` |
| Améliorer le scoring EBIOS | `evaluation/` | `evaluation/AGENTS.md` |
| Modifier les prompts d'ateliers | `prompts/` | `prompts/AGENTS.md` |
| Optimiser le RAG ChromaDB | `rag/` | `rag/AGENTS.md` |
| Configurer le modèle Ollama | `inference/` | `inference/AGENTS.md` |
| Modifier les LangChain chains | `orchestration/` | `orchestration/AGENTS.md` |
| Ajouter des tests | `tests/` | `tests/AGENTS.md` |

## Règle absolue : vérification terminologique

Avant tout commit modifiant le corpus, les prompts ou les chaînes d'évaluation,
exécuter :

```bash
python -c "
from evaluation.benchmarks.ebios_rules import FORBIDDEN_TERMS
import sys, pathlib
issues = []
for f in pathlib.Path('.').rglob('*.py'):
    text = f.read_text(errors='ignore').lower()
    for term in FORBIDDEN_TERMS:
        if term in text and 'FORBIDDEN' not in f.read_text():
            issues.append(f'{f}: contient \"{term}\"')
if issues:
    print('\\n'.join(issues)); sys.exit(1)
print('✓ Aucun terme EBIOS 2010 détecté')
"
```

## Commande de démarrage rapide pour un nouvel agent

```bash
# 1. Lire le contexte
cat CLAUDE.md

# 2. Vérifier l'état de l'environnement
make health

# 3. Lancer les tests unitaires
make test-unit

# 4. Identifier le module concerné par la tâche
# → Lire le AGENTS.md du module concerné
```
