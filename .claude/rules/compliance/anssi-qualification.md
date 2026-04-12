---
paths:
  - "compliance/**/*"
---

# Règles qualification ANSSI EBIOS RM

## Source de vérité — NE JAMAIS redéfinir ailleurs
- `compliance/matrices/anssi_requirements.py` → 128 exigences officielles
- `compliance/matrices/compliance_matrix.py`  → matrice de couverture

## Statuts valides pour CoverageEntry
TODO | IN_PROGRESS | DONE | N/A

## Règle de mise à jour matrice
À chaque implémentation :
1. Changer le statut dans compliance_matrix.py
2. Renseigner `implemented_in` avec les chemins réels
3. Renseigner `test_ref` dès qu'un test couvre l'exigence
4. `make compliance-check` doit passer (0 erreur)

## Priorités
- P0 : bloquant qualification — traiter en premier
- P1 : important — traiter avant dépôt dossier
- P2 : optionnel ou SaaS uniquement (EXI_SNC*)

## Deux dimensions de conformité à ne pas confondre
1. Conformité LLM (M1-M5) → mesurée par `ebios_rules.py`
2. Conformité applicative (S1-S6) → mesurée par `compliance/tests/`

## Exigences SaaS (EXI_SNC*)
Marquées N/A pour le POC offline. S'appliquent uniquement en mode SaaS futur.
Ne pas modifier leur statut N/A sans discussion préalable.
