"""
atelier_checks.py — Vérifications méthodologiques spécifiques par atelier
Implémente les règles liées aux exigences ANSSI EXI_M1_* → EXI_M5_*
"""
from corpus.scripts.schema import GRAVITY_SCALE, LIKELIHOOD_SCALE


# ── EXI_M1_12 : Catégories d'impacts associables aux ER ──────
IMPACT_CATEGORIES = [
    "missions et services de l'organisme",
    "humains matériels environnementaux",
    "gouvernance",
    "financiers",
    "juridiques",
    "image et confiance",
]

# ── EXI_M3_07 : Critères grille dangerosité PP ───────────────
PP_CRITERIA = {
    "dependance": (1, 4),     # (min, max)
    "penetration": (1, 4),
    "maturite_ssi": (1, 4),
    "confiance": (1, 4),
}

# ── EXI_M3_09 : Formule dangerosité (modifiable) ─────────────
def compute_dangerostiy(dep: int, pen: int, mat: int, conf: int) -> float:
    """Formule officielle ANSSI : (Dépendance × Pénétration) / (Maturité × Confiance)"""
    if mat == 0 or conf == 0:
        raise ValueError("Maturité et Confiance ne peuvent pas être 0")
    return (dep * pen) / (mat * conf)


# ── EXI_M3_12 : Seuils zones dangerosité ─────────────────────
DANGER_ZONES = {
    "danger":   2.5,    # > 2.5 : zone de danger
    "controle": 0.9,    # 0.9 ≤ x ≤ 2.5 : zone de contrôle
    "veille":   0.2,    # 0.2 ≤ x < 0.9 : zone de veille
    # < 0.2 : hors périmètre
}


def get_danger_zone(level: float) -> str:
    """Retourne la zone de dangerosité selon le niveau calculé."""
    if level > DANGER_ZONES["danger"]:
        return "danger"
    elif level > DANGER_ZONES["controle"]:
        return "controle"
    elif level > DANGER_ZONES["veille"]:
        return "veille"
    return "hors_perimetre"


# ── EXI_M4_07/09/10/11 : Méthodes vraisemblance ──────────────
LIKELIHOOD_METHODS = {
    "expresse":  "Association directe vraisemblance globale V1-V4",
    "standard":  "Cotation probabilité succès par AE → Pr cumulée",
    "avancee":   "Probabilité succès + difficulté technique → matrice Pr×Diff",
}

# Matrice Pr × Difficulté (EXI_M4_11, EXI_M4_14)
# Source : fiches méthodes EBIOS RM, Fiche 8
LIKELIHOOD_MATRIX = {
    # (prob_succès, difficulte) → vraisemblance
    (4, 0): 4, (4, 1): 4, (4, 2): 3, (4, 3): 2, (4, 4): 1,
    (3, 0): 4, (3, 1): 3, (3, 2): 3, (3, 3): 2, (3, 4): 1,
    (2, 0): 3, (2, 1): 3, (2, 2): 2, (2, 3): 2, (2, 4): 1,
    (1, 0): 2, (1, 1): 2, (1, 2): 2, (1, 3): 1, (1, 4): 0,
    (0, 0): 1, (0, 1): 1, (0, 2): 1, (0, 3): 0, (0, 4): 0,
}


def compute_likelihood_advanced(prob_success: int, difficulty: int) -> int:
    """Calcule la vraisemblance selon la méthode avancée EBIOS RM (EXI_M4_14)."""
    key = (min(prob_success, 4), min(difficulty, 4))
    return LIKELIHOOD_MATRIX.get(key, 0)


# ── EXI_M5_06 : Champs obligatoires plan de traitement ───────
TREATMENT_PLAN_REQUIRED_FIELDS = [
    "mesure",         # Nom/description de la mesure
    "domaine",        # GPDR : Gouvernance | Protection | Défense | Résilience
    "responsable",    # Entité/personne responsable
    "echeance",       # Délai de mise en œuvre
    "priorite",       # Niveau de priorité
    "statut",         # TODO | EN_COURS | TERMINE
]

TREATMENT_DOMAINS = ["gouvernance", "protection", "défense", "résilience"]


# ── EXI_M3_21 : Cohérence gravité scénario ↔ ER ─────────────
def check_scenario_gravity_consistency(
    scenario_gravity: str, er_gravities: list[str]
) -> bool:
    """
    EXI_M3_21 : La gravité d'un scénario stratégique DOIT correspondre
    à la gravité de l'événement redouté le plus grave impliqué.
    """
    if not er_gravities:
        return False
    gravity_order = list(GRAVITY_SCALE.keys())
    max_er_gravity = max(er_gravities, key=lambda g: gravity_order.index(g)
                         if g in gravity_order else -1)
    return scenario_gravity == max_er_gravity


# ── EXI_M2_10 : Cohérence ER (A1) ↔ SR/OV (A2) ─────────────
def check_er_srov_coverage(
    er_list: list[str], srov_objectives: list[str]
) -> dict:
    """
    EXI_M2_10 : Vérifie que chaque ER de l'atelier 1 est associé
    à au moins un objectif visé de l'atelier 2.
    """
    uncovered_er = [er for er in er_list
                    if not any(ov in er.lower() for ov in
                               [o.lower() for o in srov_objectives])]
    return {
        "covered": len(er_list) - len(uncovered_er),
        "total": len(er_list),
        "uncovered": uncovered_er,
        "ok": len(uncovered_er) == 0,
    }
