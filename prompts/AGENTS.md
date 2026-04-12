# AGENTS.md — prompts/

## Rôle de ce module

Définir l'ensemble des prompts hiérarchiques utilisés par la couche orchestration.
Chaque fichier contient le template pour un atelier ou une fonction spécifique.

## Hiérarchie des prompts (3 niveaux)

```
Niveau 1 : system/system_prompt.py     → Identité + contraintes absolues
Niveau 2 : ateliers/A{1-5}_*.py        → Template spécifique par atelier
Niveau 3 : validation/guard_prompt.py  → Vérification conformité post-génération
```

## Variables dynamiques communes à tous les templates

```python
COMMON_VARS = {
    "system_prompt":       str,   # Depuis system/system_prompt.py
    "rag_context":         str,   # Chunks ChromaDB formatés
    "organisation":        str,   # Description de l'organisation
    "secteur":             str,   # Secteur d'activité
    "historique_session":  str,   # Mémoire LangChain (ateliers précédents)
}
```

## Variables spécifiques par atelier

```python
A1_VARS = ["perimetre", "hypotheses", "participants", "duree_cycle_strategique",
           "referentiels", "etape"]
A2_VARS = ["missions_a1", "valeurs_metier_a1", "evenements_redoutes_a1"]
A3_VARS = ["vm_bs_a1", "er_a1", "srov_a2", "parties_prenantes"]
A4_VARS = ["bs_socle_a1", "scenarios_a3", "ppc_a3", "methode_vraisemblance"]
A5_VARS = ["mesures_existantes", "scenarios_risque"]
```

## Températures recommandées par atelier

```python
ATELIER_TEMPERATURES = {
    "A1": 0.2,   # Structuration précise, terminologie normalisée
    "A2": 0.3,   # Légère créativité pour variété des SR
    "A3": 0.4,   # Modélisation adversariale (attaquant)
    "A4": 0.35,  # Technique + créatif (modes opératoires)
    "A5": 0.2,   # Cohérence stricte avec ateliers précédents
}
```

## Contraintes terminologiques dans les prompts

Toujours inclure dans le system prompt les termes REQUIS et INTERDITS.
Référencer `../evaluation/benchmarks/ebios_rules.py` pour la liste complète.

## Tests des prompts (tests/test_prompts.py)

Chaque template doit passer les tests :
1. Toutes les variables sont présentes (pas de KeyError)
2. Le rendu contient les termes EBIOS requis
3. La longueur du prompt final < 4096 tokens (marge pour le contexte RAG)
