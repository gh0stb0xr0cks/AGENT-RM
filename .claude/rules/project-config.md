---
paths:
  - "pyproject.toml"
  - "Makefile"
  - "docker-compose.yml"
  - ".github/**/*"
---

# Configuration projet — Dépendances et CI

## Groupes de dépendances pyproject.toml
- `[project.dependencies]`     → runtime obligatoire (LangChain, ChromaDB, FastAPI…)
- `[project.optional-dependencies.dev]`     → dev/test uniquement (pytest, ruff)
- `[project.optional-dependencies.unsloth]` → GPU training (ne pas inclure dans runtime)

## Avant d'ajouter une dépendance
1. Vérifier qu'elle est compatible mode offline (pas de telemetry par défaut)
2. Vérifier la licence (Apache 2.0 / MIT / BSD préférés)
3. Vérifier qu'elle n'introduit pas d'appel réseau automatique au démarrage
4. Ajouter dans le bon groupe (runtime vs dev vs unsloth)

## Makefile — cibles obligatoires (ne pas supprimer)
`setup` · `build-corpus` · `train` · `merge-export` · `evaluate`
`build-rag` · `test` · `test-unit` · `serve` · `compliance-check`

## CI GitHub Actions (.github/workflows/)
- `ci.yml`   → lint (ruff) + test-unit à chaque push
- `eval.yml` → benchmark EBIOS RM complet (déclenché manuellement)
Pas de secrets dans les workflows — tout fonctionne en local sans token.
