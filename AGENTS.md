# Navigation rapide — LLM EBIOS RM

Lire CLAUDE.md en premier. Ce fichier est un index de navigation uniquement.

## Par tâche → module + rule activée

| Tâche | Module | Rule déclenchée |
|-------|--------|-----------------|
| Générer ou modifier des exemples corpus | `corpus/` | `.claude/rules/corpus/corpus-pipeline.md` |
| Scripts de training / merge / quantif | `finetuning/` | `.claude/rules/finetuning/training-params.md` |
| Scoring, benchmark, rapport | `evaluation/` | `.claude/rules/finetuning/evaluation.md` |
| ChromaDB, embeddings, retrieval | `rag/` | `.claude/rules/orchestration/langchain-chains.md` |
| Prompts ateliers A1→A5, guard | `prompts/` | `.claude/rules/orchestration/langchain-chains.md` |
| LangChain chains, mémoire session | `orchestration/` | `.claude/rules/orchestration/langchain-chains.md` |
| Ollama Modelfile, LM Studio config | `inference/` | `.claude/rules/inference/inference-config.md` |
| FastAPI routes, auth, logging | `app/api/` | `.claude/rules/app/api-security.md` |
| Matrice conformité ANSSI | `compliance/` | `.claude/rules/compliance/anssi-qualification.md` |
| Tests unitaires, intégration, e2e | `tests/` | `.claude/rules/tests/testing-standards.md` |

## Vérification terminologique avant commit
```bash
make compliance-check
```
