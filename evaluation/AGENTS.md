# AGENTS.md — evaluation/

## Rôle de ce module

Mesurer la conformité méthodologique du modèle fine-tuné sur les 5 ateliers EBIOS RM.
Produire le rapport de validation L6 cosigné par l'expert EBIOS certifié.

## Architecture du scoring

```
benchmarks/ebios_rules.py    → Règles de validation (terminologie, échelles, structure)
benchmarks/atelier_checks.py → Checks spécifiques par atelier (A1→A5)
scripts/score_terminology.py → Score terminologie ANSSI (automatique)
scripts/score_structure.py   → Score structure livrables (automatique)
scripts/score_coherence.py   → Score cohérence inter-ateliers (automatique)
scripts/run_benchmark.py     → Orchestrateur : lance tous les checks
scripts/generate_report.py   → Génère le rapport PDF (livrable L6)
```

## Métriques et seuils (jalon J4 — semaine 10)

| Métrique | Seuil minimal | Seuil cible | Méthode |
|---------|--------------|------------|---------|
| Conformité globale EBIOS RM | 75% | ≥80% | Benchmark 500 cas |
| Terminologie officielle ANSSI | 90% | ≥95% | Script automatique |
| Cohérence inter-ateliers A1→A5 | 80% | ≥85% | Expert certifié |
| Taux hallucinations factuelles | ≤10% | ≤5% | Review 200 outputs |
| Couverture 5 ateliers | 100% | 100% | 1 prompt/atelier |

## Règles EBIOS RM (ebios_rules.py)

```python
REQUIRED_TERMS = [
    "valeurs métier", "biens supports", "événements redoutés",
    "sources de risque", "objectifs visés", "parties prenantes"
]

FORBIDDEN_TERMS = [
    "biens essentiels", "actifs", "menaces principales",
    "PACS", "risques cyber", "attaquants"
]

GRAVITY_SCALE = ["G1", "G2", "G3", "G4", "Mineure", "Significative", "Grave", "Critique"]
LIKELIHOOD_SCALE = ["V1", "V2", "V3", "V4", "Peu vraisemblable", "Vraisemblable",
                    "Très vraisemblable", "Quasi-certain"]

ATELIER_REQUIRED_FIELDS = {
    "A1": ["valeurs métier", "biens supports", "événements redoutés", "gravité", "socle"],
    "A2": ["sources de risque", "objectifs visés", "motivation", "ressources", "pertinence"],
    "A3": ["scénarios stratégiques", "chemins d'attaque", "parties prenantes critiques", "gravité"],
    "A4": ["scénarios opérationnels", "vraisemblance", "actions élémentaires", "mode opératoire"],
    "A5": ["plan de traitement", "risques résiduels", "responsable", "échéance"]
}
```

## Jeux de test (testsets/)

- `A{1-5}_*.jsonl` : 500 cas par atelier, jamais vus pendant l'entraînement
- Format identique au corpus (ChatML) mais sans le turn "assistant" (à générer)
- Référence : colonne "expected" dans chaque fichier JSONL

## Ne PAS utiliser testsets/ pendant le fine-tuning (data leakage)

Les fichiers testsets/ sont la source de vérité pour l'évaluation finale.
Ils ne doivent JAMAIS être chargés dans corpus/datasets/.
