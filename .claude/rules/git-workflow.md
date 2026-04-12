# Workflow Git & Makefile — LLM EBIOS RM

## Branches
- `main`    → code stable uniquement, protégée (pas de push direct)
- `dev`     → branche de développement principale
- `feat/*`  → features, merge vers dev via PR
- `fix/*`   → corrections, merge vers dev via PR
- `corpus/` → branches dédiées aux ajouts corpus (ex: `corpus/add-sante-examples`)

## Convention de commits (Conventional Commits)
```
feat(corpus): add 150 A3 examples for energy sector
fix(ebios): replace "biens essentiels" with "valeurs métier" in A1 prompt
chore(finetuning): update lora_alpha to 32 in training_args.yaml
docs(compliance): mark EXI_M1_07 as IN_PROGRESS
test(unit): add test_no_forbidden_terms for corpus filter
```
Préfixes valides : feat · fix · docs · test · chore · refactor · perf

## Avant chaque commit
```bash
make compliance-check   # 0 erreur obligatoire
make test-unit          # tous les tests P0 doivent passer
ruff check .            # 0 erreur de lint
```

## À ne jamais committer
- `.env` (secrets)
- `finetuning/checkpoints/` (trop volumineux)
- `finetuning/output/*.gguf` → utiliser Git LFS
- `data/chroma_db/` (régénérable via `make build-rag`)
- `data/session_cache/`
- `corpus/datasets/*.jsonl` → Git LFS ou livraison directe

## Git LFS — fichiers à tracker
```
*.gguf linguist-generated=true
*.bin  linguist-generated=true
```
