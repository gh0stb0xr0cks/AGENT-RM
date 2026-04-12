# Préférences personnelles — Cross-projets

## Langue de travail
- Code et commentaires : français pour les projets EBIOS RM, anglais sinon
- Docstrings : français pour les fonctions métier EBIOS, anglais pour l'infra
- Git commits : anglais (Conventional Commits)

## Style de code Python
- Longueur de ligne max : 100 caractères
- Docstrings format Google
- Type hints obligatoires sur toutes les fonctions publiques
- Pas de `print()` en production → utiliser `logging`

## Préférences de réponse agent
- Toujours montrer les commandes exactes à exécuter, pas juste la description
- Si un fichier source de vérité existe dans le projet, le citer avant de répondre
- Signaler explicitement si une modification peut casser un test existant
- Préférer des fonctions courtes et testables aux classes complexes

## Habitudes de workflow
- Vérifier `make compliance-check` avant toute suggestion de commit
- Proposer la mise à jour de compliance_matrix.py quand une exigence ANSSI est couverte
- Toujours proposer le test unitaire correspondant avec le code produit
