# AGENTS.md — compliance/

## Rôle de ce module

Assurer la traçabilité complète des 128 exigences ANSSI EBIOS RM
vis-à-vis du code du projet. Préparer la qualification ANSSI.

## Fichiers clés

```
matrices/anssi_requirements.py  → SOURCE DE VÉRITÉ des 128 exigences (libellés officiels)
matrices/compliance_matrix.py   → MATRICE DE COUVERTURE : statut + modules couvrants
scripts/run_compliance_check.py → Vérifie que tous les fichiers "implemented_in" existent
scripts/generate_conformity_report.py → Génère le rapport PDF de conformité
tests/                          → Tests automatisés par catégorie d'exigence
docs/QUALIFICATION_GUIDE.md     → Guide de préparation au dossier de qualification ANSSI
```

## Comment mettre à jour la matrice

Quand une exigence est implémentée :

```python
# Dans compliance/matrices/compliance_matrix.py, trouver l'entrée par ref
# Ex : passer EXI_M1_02 de TODO à IN_PROGRESS puis DONE
CoverageEntry("EXI_M1_02", "DONE",           # ← modifier ici
              implemented_in=["app/api/routes.py"],
              test_ref="tests/compliance/test_exi_m1.py::test_M1_02")
```

Puis lancer `make compliance-check` pour vérifier la cohérence.

## Commandes

```bash
make compliance-check   # Vérifie cohérence matrice (fichiers existent, tests référencés)
make compliance-report  # Génère rapport PDF pour dossier ANSSI
python compliance/matrices/compliance_matrix.py  # Affiche les stats de couverture
```

## Priorités (P0 = bloquantes pour la qualification)

- **P0** : Exigences fonctionnelles critiques + toutes les S* sécurité obligatoires
- **P1** : Exigences importantes mais non rédhibitoires au premier dépôt
- **P2** : Optionnelles ou SaaS uniquement

## Mapping exigences → prompts

| Catégorie ANSSI | Module projet principal |
|----------------|------------------------|
| EXI_M1 — Atelier 1 | `prompts/ateliers/A1_cadrage.py` + `evaluation/benchmarks/atelier_checks.py` |
| EXI_M2 — Atelier 2 | `prompts/ateliers/A2_sources.py` |
| EXI_M3 — Atelier 3 | `prompts/ateliers/A3_strategique.py` + `evaluation/benchmarks/ebios_rules.py` |
| EXI_M4 — Atelier 4 | `prompts/ateliers/A4_operationnel.py` + `evaluation/benchmarks/ebios_rules.py` |
| EXI_M5 — Atelier 5 | `prompts/ateliers/A5_traitement.py` |
| EXI_S1 — Auth | `app/api/dependencies.py` |
| EXI_S2 — Confidentialité | `inference/configs/ollama_config.py` + TLS app/ |
| EXI_S3 — Journalisation | `app/api/routes.py` (middleware logging) |
| EXI_S4 — Dev policies | `.github/workflows/` + documentation |
| EXI_S5 — MCS | `compliance/docs/QUALIFICATION_GUIDE.md` |
| EXI_S6 — CGU | `compliance/docs/QUALIFICATION_GUIDE.md` |
| EXI_SNC — SaaS | Hors scope POC (N/A) |

## Note architecture : deux dimensions de conformité

1. **Conformité LLM** (ateliers M1-M5) : le modèle fine-tuné génère des sorties conformes.
   → Vérifiée par `evaluation/benchmarks/ebios_rules.py` (score_output)

2. **Conformité applicative** (M1-M5 CRUD + S1-S6 sécurité) : l'application gère les données.
   → Vérifiée par les tests `compliance/tests/` + audit ANSSI

Les deux dimensions sont NÉCESSAIRES pour la qualification.
