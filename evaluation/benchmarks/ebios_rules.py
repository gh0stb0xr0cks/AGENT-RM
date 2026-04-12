"""
ebios_rules.py — Règles de validation automatique EBIOS RM
Utilisé par le benchmark d'évaluation et le validation guard.
Source de vérité terminologique pour tout le projet.
"""
from corpus.scripts.schema import (
    REQUIRED_TERMS, FORBIDDEN_TERMS,
    GRAVITY_SCALE, LIKELIHOOD_SCALE,
    Atelier
)


# Champs obligatoires par atelier dans la réponse générée
ATELIER_REQUIRED_FIELDS = {
    Atelier.A1: [
        "valeurs métier", "biens supports", "événements redoutés",
        "gravité", "socle de sécurité",
    ],
    Atelier.A2: [
        "sources de risque", "objectifs visés",
        "motivation", "ressources", "pertinence",
    ],
    Atelier.A3: [
        "scénarios stratégiques", "chemins d'attaque",
        "parties prenantes critiques", "gravité",
    ],
    Atelier.A4: [
        "scénarios opérationnels", "vraisemblance",
        "actions élémentaires", "mode opératoire",
    ],
    Atelier.A5: [
        "plan de traitement", "risques résiduels",
        "responsable", "échéance",
    ],
}

# Volumétrie ANSSI par atelier (pour vérification cohérence)
ATELIER_VOLUMETRY = {
    Atelier.A1: {"valeurs_metier": (5, 10)},   # min, max
    Atelier.A2: {"couples_srov": (3, 6)},
    Atelier.A3: {"chemins_attaque_per_srov": (1, 3)},
    Atelier.A4: {"scenarios_operationnels": (1, None)},
    Atelier.A5: {"mesures_securite": (1, None)},
}

# Poids pour le score global
SCORING_WEIGHTS = {
    "terminologie": 0.40,   # Termes ANSSI corrects
    "structure":    0.40,   # Champs requis présents
    "echelles":     0.20,   # Scales G/V utilisées
}

# Seuils d'acceptation (jalon J4)
ACCEPTANCE_THRESHOLDS = {
    "global":       0.80,   # ≥80% conformité globale
    "terminologie": 0.95,   # ≥95% terminologie correcte
    "coherence":    0.85,   # ≥85% cohérence inter-ateliers
    "hallucinations": 0.05, # ≤5% hallucinations factuelles
}


def score_output(output: str, atelier: Atelier) -> dict:
    """
    Score automatique d'une réponse EBIOS RM.
    Retourne un dict avec les scores par dimension et le score global.
    """
    text_lower = output.lower()

    # Score terminologie
    required_found = sum(1 for t in REQUIRED_TERMS if t in text_lower)
    forbidden_found = sum(1 for t in FORBIDDEN_TERMS if t in text_lower)
    term_score = (required_found / len(REQUIRED_TERMS)) * (
        1 - min(forbidden_found, len(FORBIDDEN_TERMS)) / len(FORBIDDEN_TERMS)
    )

    # Score structure
    required_fields = ATELIER_REQUIRED_FIELDS.get(atelier, [])
    struct_score = sum(1 for f in required_fields if f.lower() in text_lower)
    struct_score = struct_score / len(required_fields) if required_fields else 0

    # Score échelles
    all_gravity = list(GRAVITY_SCALE.keys()) + list(GRAVITY_SCALE.values())
    all_likelihood = list(LIKELIHOOD_SCALE.keys()) + list(LIKELIHOOD_SCALE.values())
    has_gravity = any(s in output for s in all_gravity)
    has_likelihood = any(s in output for s in all_likelihood)
    scale_score = (int(has_gravity) + int(has_likelihood)) / 2

    global_score = (
        term_score * SCORING_WEIGHTS["terminologie"]
        + struct_score * SCORING_WEIGHTS["structure"]
        + scale_score * SCORING_WEIGHTS["echelles"]
    )

    return {
        "atelier": atelier.value,
        "terminologie": round(term_score, 3),
        "structure": round(struct_score, 3),
        "echelles": round(scale_score, 3),
        "global": round(global_score, 3),
        "forbidden_terms_found": forbidden_found,
        "passed": global_score >= ACCEPTANCE_THRESHOLDS["global"],
    }
