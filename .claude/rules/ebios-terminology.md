# Terminologie EBIOS RM 2024 — Règles absolues

S'applique à tout le projet : code, commentaires, prompts, corpus, docs.

## Termes requis dans les sorties LLM (au moins 2/4 présents)
- valeurs métier
- biens supports
- événements redoutés
- sources de risque

## Termes interdits — lever une alerte si détectés
biens essentiels | actifs critiques | actifs | menaces (seul)
PACS | plan d'amélioration continue | risques cyber | attaquants

## Échelles officielles (ne jamais inventer d'autres niveaux)
- Gravité   : G1 Mineure · G2 Significative · G3 Grave · G4 Critique
- Vraisemblance : V1 Peu vraisemblable · V2 Vraisemblable · V3 Très vraisemblable · V4 Quasi-certain
- Dangerosité PP : (Dépendance × Pénétration) / (Maturité SSI × Confiance)

## Vérification automatique
```bash
python evaluation/benchmarks/ebios_rules.py
```
