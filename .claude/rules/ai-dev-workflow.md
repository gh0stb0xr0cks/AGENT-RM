# Workflow développement IA-assisté — OpenCode

## Ordre de travail recommandé sur une nouvelle tâche
1. Lire le AGENTS.md → identifier le module concerné
2. Lire la rule ciblée dans `.claude/rules/` → contraintes spécifiques
3. Lire le fichier source de vérité du module (schema.py, ebios_rules.py…)
4. Implémenter → tester → mettre à jour compliance_matrix.py si applicable

## Ce que l'agent NE doit pas faire sans validation humaine
- Modifier les hyperparamètres LoRA (lora_r, lora_alpha) sans justification
- Changer les seuils d'évaluation dans `ACCEPTANCE_THRESHOLDS`
- Modifier le statut d'une exigence P0 de DONE → TODO
- Ajouter un terme au corpus sans passer par `04_quality_filter.py`
- Lancer `make train` en mode non-supervisé

## Fichiers à lire avant de toucher à un module
| Module modifié | Lire d'abord |
|---------------|-------------|
| `corpus/` | `corpus/scripts/schema.py` |
| `finetuning/` | `finetuning/configs/training_args.yaml` |
| `evaluation/` | `evaluation/benchmarks/ebios_rules.py` |
| `compliance/` | `compliance/matrices/anssi_requirements.py` |
| `orchestration/` | `orchestration/chains/rag_chain.py` |

## Signalement obligatoire
Si une modification risque de faire régresser un test P0 ou de changer
un comportement lié à une exigence ANSSI P0 : **signaler explicitement
avant d'implémenter**, pas après.

## Gestion des ambiguïtés terminologiques EBIOS
En cas de doute sur un terme : consulter
`docs/ebios/guide_ebios_rm_2024.pdf` → section "Termes et Définitions".
Ne jamais inventer de terminologie.
