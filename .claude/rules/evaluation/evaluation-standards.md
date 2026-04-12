---
paths:
  - "evaluation/**/*"
---

# Règles d'évaluation EBIOS RM

## Seuils d'acceptation (jalon J4 — M12)
```python
ACCEPTANCE_THRESHOLDS = {
    "global":        0.80,   # ≥ 80 % conformité globale
    "terminologie":  0.95,   # ≥ 95 % termes ANSSI corrects
    "coherence":     0.85,   # ≥ 85 % cohérence inter-ateliers
    "hallucinations": 0.05,  # ≤ 5 % hallucinations factuelles
}
```

## Poids du score global (ebios_rules.py)
- Terminologie : 40 %
- Structure     : 40 %
- Échelles      : 20 %

## Règle critique sur testsets/
Les fichiers `testsets/A*.jsonl` sont le holdout final.
NE JAMAIS les inclure dans corpus/datasets/ (data leakage).
NE JAMAIS les utiliser pendant le training ni la validation.

## Commandes d'évaluation
```bash
make evaluate              # Benchmark complet (500 cas/atelier)
python evaluation/scripts/run_benchmark.py  # Script direct
```

## Champs obligatoires par atelier (atelier_checks.py)
- A1 : valeurs métier · biens supports · événements redoutés · gravité · socle
- A2 : sources de risque · objectifs visés · motivation · ressources · pertinence
- A3 : scénarios stratégiques · chemins d'attaque · PPC · gravité
- A4 : scénarios opérationnels · vraisemblance · actions élémentaires
- A5 : plan de traitement · risques résiduels · responsable · échéance
