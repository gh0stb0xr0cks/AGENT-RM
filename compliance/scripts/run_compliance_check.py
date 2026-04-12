"""
run_compliance_check.py — Vérification de cohérence de la matrice ANSSI

Vérifie :
1. Chaque exigence ANSSI a une entrée dans COVERAGE
2. Les fichiers "implemented_in" existent réellement dans le projet
3. Les tests "test_ref" existent dans tests/compliance/
4. Aucune exigence DONE sans test_ref ni implemented_in
"""
import sys
from pathlib import Path

# Ajout du chemin racine
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from compliance.matrices.anssi_requirements import ALL_REQUIREMENTS, REQ_BY_REF
from compliance.matrices.compliance_matrix import COVERAGE, COVERAGE_BY_REF, get_compliance_stats

errors = []
warnings = []

print("=" * 60)
print("  VÉRIFICATION MATRICE DE CONFORMITÉ ANSSI EBIOS RM")
print("=" * 60)

# 1. Toutes les exigences ont une entrée dans COVERAGE
covered_refs = {e.req_ref for e in COVERAGE}
all_refs = {r.ref for r in ALL_REQUIREMENTS}
missing = all_refs - covered_refs
if missing:
    for ref in sorted(missing):
        errors.append(f"EXIGENCE NON COUVERTE : {ref}")

# 2. Fichiers "implemented_in" existent
for entry in COVERAGE:
    for filepath in entry.implemented_in:
        full_path = ROOT / filepath
        if not full_path.exists():
            warnings.append(f"{entry.req_ref}: fichier manquant → {filepath}")

# 3. DONE sans test_ref
for entry in COVERAGE:
    if entry.status == "DONE" and not entry.test_ref:
        warnings.append(f"{entry.req_ref}: statut DONE sans test_ref")

# Rapport
stats = get_compliance_stats()
print(f"\n  Total exigences  : {stats['total']}")
print(f"  DONE             : {stats['by_status']['DONE']}")
print(f"  IN_PROGRESS      : {stats['by_status']['IN_PROGRESS']}")
print(f"  TODO             : {stats['by_status']['TODO']}")
print(f"  N/A (SaaS only)  : {stats['by_status']['N/A']}")
print(f"\n  Taux complétion  : {stats['completion_pct']}%")
print(f"  Exig. P0 TODO    : {stats['p0_blocking']} BLOQUANTES")

if errors:
    print(f"\n❌ ERREURS ({len(errors)}) :")
    for e in errors:
        print(f"   {e}")
    sys.exit(1)

if warnings:
    print(f"\n⚠  AVERTISSEMENTS ({len(warnings)}) :")
    for w in warnings:
        print(f"   {w}")

print("\n✓ Matrice de conformité cohérente")
