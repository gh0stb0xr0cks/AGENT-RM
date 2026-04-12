"""
anssi_requirements.py — Référentiel complet des exigences ANSSI EBIOS RM
Source : ANSSI-Exigences-dev-EBIOS-RM.xlsx (128 exigences)

Ce fichier est la SOURCE DE VÉRITÉ pour toutes les vérifications de conformité.
NE PAS modifier les descriptions — elles reproduisent exactement le libellé ANSSI.

Catégories :
  M1-M5 : Exigences Méthodologiques (fonctionnelles, par atelier)
  S1-S6 : Exigences de Sécurité (transversales)
  SNC1-SNC4 : Exigences SaaS / SecNumCloud (mode hébergé uniquement)
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RequirementCategory(str, Enum):
    # Exigences méthodologiques
    M1_CADRAGE   = "M1"   # Atelier 1 – Cadrage et socle de sécurité
    M2_SOURCES   = "M2"   # Atelier 2 – Sources de risque
    M3_STRATEGIQUE = "M3" # Atelier 3 – Scénarios stratégiques
    M4_OPERATIONNEL = "M4"# Atelier 4 – Scénarios opérationnels
    M5_TRAITEMENT = "M5"  # Atelier 5 – Traitement du risque
    # Exigences de sécurité
    S1_AUTH      = "S1"   # Identification & Authentification
    S2_CONFIDENTIALITY = "S2"  # Confidentialité des données
    S3_LOGGING   = "S3"   # Journalisation
    S4_DEV       = "S4"   # Revue politiques internes – Développement
    S5_MCS       = "S5"   # Maintien en conditions de sécurité
    S6_CGU       = "S6"   # Conditions générales d'emploi & usage
    # Exigences SaaS / SecNumCloud
    SNC1_HOSTING = "SNC1" # Hébergement qualifié SecNumCloud
    SNC2_ADMIN   = "SNC2" # Administration sécurisée
    SNC3_SEGMENT = "SNC3" # Segmentation client
    SNC4_CRYPTO  = "SNC4" # Chiffrement éléments hébergés


class RequirementScope(str, Enum):
    """Périmètre d'application de l'exigence."""
    ALL          = "all"       # Toutes configurations (local + SaaS)
    SAAS_ONLY    = "saas_only" # SaaS uniquement (exigences SNC*)
    OPTIONAL     = "optional"  # Exigence optionnelle (mention "Optionnel" dans libellé)


@dataclass
class Requirement:
    ref: str                            # Ex: "EXI_M1_01"
    description: str                    # Libellé exact ANSSI
    category: RequirementCategory
    section: str                        # Section ANSSI originale
    scope: RequirementScope = RequirementScope.ALL
    optional: bool = False
    # Champs de suivi projet (remplis par compliance_matrix.py)
    status: str = "TODO"                # TODO | IN_PROGRESS | DONE | N/A
    implemented_in: list[str] = field(default_factory=list)  # Fichiers/modules
    test_ref: str = ""                  # Référence du test couvrant l'exigence
    notes: str = ""


# ══════════════════════════════════════════════════════
# ATELIER 1 — Cadrage et socle de sécurité (23 exigences)
# ══════════════════════════════════════════════════════
M1_REQUIREMENTS = [
    Requirement("EXI_M1_01", "L'application permet de renseigner les éléments du cadre de l'étude : objectifs, participants, cadre temporel, contraintes, hypothèses et planning projet.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_02", "L'utilisateur peut ajouter, modifier, supprimer les éléments du cadre de l'étude.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_03", "L'application prévoit d'éditer ou d'exporter les éléments du cadre de l'étude.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_04", "L'application permet de recenser les missions de l'objet étudié avec description.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_05", "L'application permet de recenser les valeurs métier associées à l'objet, avec dénomination, nature et description, ainsi que le propriétaire.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_06", "L'application recense les biens supports associés à chaque valeur métier avec dénomination, description et propriétaire.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_07", "L'utilisateur peut ajouter, modifier, supprimer des éléments du périmètre métier‑technique.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_08", "L'application prévoit d'éditer, d'importer ou d'exporter les éléments du périmètre métier‑technique (avec filtres optionnels).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_09", "L'application prévoit d'ajouter, modifier et supprimer des événements redoutés.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_10", "L'application permet d'associer à chaque valeur métier un ou plusieurs événements redoutés.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_11", "L'application propose une échelle de gravité paramétrable (création, mise à jour, suppression).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_12", "À une valeur métier et un événement redouté peuvent être associés un ou plusieurs impacts (juridique, financier, image…).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_13", "L'application permet d'associer à chaque couple valeur métier / événement redouté un niveau de gravité de l'échelle.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_14", "L'application permet de tracer les justifications des impacts (champ texte, colonne supplémentaire…).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_15", "L'application permet d'ajouter un événement redouté non lié à une valeur métier (risques non‑intentionnels) avec évaluation express.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_16", "L'application prévoit d'éditer ou d'exporter les événements redoutés.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_17", "L'application permet à l'utilisateur de renseigner manuellement les référentiels et exigences de sécurité associés.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_18", "Pour chaque référentiel, l'application propose de sélectionner les exigences respectées via cases à cocher multisélection.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_19", "L'application permet de rendre visible ou non le détail des exigences par simple clic.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_20", "Un indicateur visuel (ex. couleur) montre l'état d'application des référentiels (vert, orange, rouge).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_21", "Pour chaque exigence, l'utilisateur peut saisir commentaires ou justifications de dérogation.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_22", "L'utilisateur peut ajouter, modifier, supprimer les référentiels de sécurité et leurs états d'application.",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
    Requirement("EXI_M1_23", "L'application prévoit d'éditer ou d'exporter le socle de sécurité (avec filtres optionnels).",
                RequirementCategory.M1_CADRAGE, "Atelier 1 – Cadrage et socle de sécurité"),
]

# ══════════════════════════════════════════════════════
# ATELIER 2 — Sources de risque (10 exigences)
# ══════════════════════════════════════════════════════
M2_REQUIREMENTS = [
    Requirement("EXI_M2_01", "L'application propose par défaut des catégories génériques de sources de risques et d'objectifs visés.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_02", "L'application permet de compléter ou modifier ces catégories (ajout, suppression, renommage).",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_03", "L'utilisateur saisit manuellement les objectifs visés pour chaque source de risque identifiée.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_04", "Chaque couple source‑risque/objectif visé possède des critères de caractérisation (motivation, ressources, activité).",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_05", "L'application évalue le niveau de pertinence du couple via une métrique ou saisie directe.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_06", "L'application trace les justifications des cotations de pertinence (champ texte, colonne supplémentaire…).",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_07", "L'application prévoit d'éditer et d'exporter les couples source‑risque/objectif visé et leur évaluation.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_08", "L'application propose de sélectionner les couples retenus pour la suite de l'analyse.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_09", "L'application permet de représenter les couples sur des cartographies radar.",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
    Requirement("EXI_M2_10", "L'application permet le rapprochement entre événements redoutés (atelier 1) et couples SR/OV (atelier 2).",
                RequirementCategory.M2_SOURCES, "Atelier 2 – Sources de risque"),
]

# ══════════════════════════════════════════════════════
# ATELIER 3 — Scénarios stratégiques (28 exigences)
# ══════════════════════════════════════════════════════
M3_REQUIREMENTS = [
    Requirement("EXI_M3_01", "L'application propose par défaut des catégories génériques de parties prenantes (internes/externe).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_02", "L'utilisateur peut ajouter, modifier, supprimer les catégories des parties prenantes.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_03", "Optionnel : import/fusion de bases de connaissances des catégories de parties prenantes.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques", optional=True),
    Requirement("EXI_M3_04", "L'utilisateur recense les parties prenantes avec nom, description et catégorie.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_05", "À chaque partie prenante sont associées deux valeurs : dangerosité initiale et résiduelle.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_06", "L'application calcule le niveau de dangerosité initiale à partir de critères et métriques d'évaluation.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_07", "Grille d'évaluation par défaut : dépendance, pénétration, maturité SSI, confiance.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_08", "Ajout/modif/suppression des métriques de cotation est possible.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_09", "Formule calcul : (Dépendance × Pénétration) / (Maturité SSI × Confiance) (modifiable).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_10", "L'application trace les justifications des cotations des niveaux de dangerosité.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_11", "Le niveau de dangerosité initiale peut être « forcé » manuellement.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_12", "Saisie des seuils correspondant aux zones danger, contrôle et veille.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_13", "Représentation radar du niveau de dangerosité initiale des parties prenantes.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_14", "L'utilisateur peut sélectionner les parties prenantes critiques (visuellement distinguées).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_15", "Ajout/modif/suppression des parties prenantes, critères et seuils avec indication visuelle des modifications intentionnelles.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_16", "Si atelier 4 absent, proposer la pertinence du couple SR/OV pour obtenir la vraisemblance du scénario stratégique.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_17", "L'application prévoit d'éditer et d'exporter la cartographie de dangerosité initiale (filtres optionnels).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_18", "Construction des scénarios stratégiques avec chemins d'attaque associés (nom, description).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_19", "Chaque scénario stratégique est lié à un couple SR/OV et séquence d'évènements (parties prenantes ou valeurs métier).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_20", "Optionnel : glisser‑déposer d'évènements pour construire les scénarios.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques", optional=True),
    Requirement("EXI_M3_21", "La gravité d'un scénario stratégique correspond à la gravité des événements redoutés impliqués.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_22", "Il est possible de « forcer » le niveau de gravité d'un scénario stratégique.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_23", "L'application prévoit d'éditer et d'exporter les scénarios stratégiques avec leurs chemins d'attaque (filtres optionnels).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_24", "Association à chaque partie prenante de mesures de sécurité ou niveau cible lié aux critères d'évaluation.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_25", "Calcul du niveau de dangerosité résiduel après application des mesures (même formule que pour le niveau initial).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_26", "Représentation radar du niveau de dangerosité résiduel des parties prenantes.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_27", "Les seuils zones danger/contrôle/veille sont identiques sur les cartographies initiale et résiduelle.",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
    Requirement("EXI_M3_28", "Édition/exportation de la cartographie résiduelle et du tableau synthèse des mesures (filtres optionnels).",
                RequirementCategory.M3_STRATEGIQUE, "Atelier 3 – Scénarios stratégiques"),
]

# ══════════════════════════════════════════════════════
# ATELIER 4 — Scénarios opérationnels (18 exigences)
# ══════════════════════════════════════════════════════
M4_REQUIREMENTS = [
    Requirement("EXI_M4_01", "Construction des scénarios opérationnels liés aux scénarios stratégiques (nom, description, lien).",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_02", "Optionnel : interface intuitive avec glisser‑déposer d'actions élémentaires.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels", optional=True),
    Requirement("EXI_M4_03", "Liste par défaut d'actions élémentaires organisées par catégories, modifiable par l'utilisateur.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_04", "Optionnel : import/fusion de bases de connaissances d'actions élémentaires.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels", optional=True),
    Requirement("EXI_M4_05", "Chaque action élémentaire est associée à un bien support concerné.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_06", "Ajout d'opérateurs ET/OU dans les modes opératoires des scénarios opérationnels.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_07", "Sélection du mode d'évaluation de vraisemblance (expresse, standard, avancée) appliqué à tous les scénarios opérationnels.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_08", "Possibilité de changer à tout moment la méthode d'évaluation de vraisemblance.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_09", "Méthode expresse : association d'une vraisemblance globale au scénario (et éventuellement aux modes opératoires).",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_10", "Méthode standard : association d'une probabilité de succès à chaque action élémentaire.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_11", "Méthode avancée : association d'une probabilité de succès et d'une difficulté technique à chaque action élémentaire.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_12", "Grilles génériques par défaut pour vraisemblance globale, probabilité et difficulté, modifiables par l'utilisateur.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_13", "Optionnel : importation de métriques de cotation personnalisées.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels", optional=True),
    Requirement("EXI_M4_14", "Algorithmes calculs vraisemblance globale à partir des cotations (standard/avancée) sélectionnables.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_15", "Facilitation de la cotation via une base de connaissances éditable par l'utilisateur.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_16", "La vraisemblance globale d'un scénario opérationnel peut être « forcée ».",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_17", "Identification/visualisation des actions élémentaires les plus critiques et du mode opératoire le plus vraisemblable.",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
    Requirement("EXI_M4_18", "Édition/exportation des scénarios opérationnels et tableau synthèse (avec filtres optionnels).",
                RequirementCategory.M4_OPERATIONNEL, "Atelier 4 – Scénarios opérationnels"),
]

# ══════════════════════════════════════════════════════
# ATELIER 5 — Traitement du risque (12 exigences)
# ══════════════════════════════════════════════════════
M5_REQUIREMENTS = [
    Requirement("EXI_M5_01", "Visualisation de la cartographie du risque initial (gravité vs vraisemblance).",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_02", "Édition/exportation de la cartographie du risque initial et tableau synthèse (filtres optionnels).",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_03", "Optionnel : édition d'une matrice traçabilité entre événements redoutés et scénarios traités.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque", optional=True),
    Requirement("EXI_M5_04", "Association d'un indicateur couleur (vert/orange/rouge) représentant la stratégie de traitement du risque pour chaque scénario.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_05", "Association aux scénarios de mesures de sécurité applicables à l'objet ou aux parties prenantes.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_06", "Pour chaque mesure : catégorie, élément concerné, responsable, coût, échéance, pourcentage d'avancement, commentaires.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_07", "Édition/exportation du plan de traitement du risque avec possibilités de tri/filtres.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_08", "Réévaluation des gravités/vraisemblances résiduelles après mesures (glissement manuel ou tableau).",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_09", "Possibilité de « forcer » les valeurs résiduelles de gravité et vraisemblance.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_10", "Visualisation de la cartographie du risque résiduel (mêmes échelles que le risque initial).",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_11", "Édition/exportation de la cartographie du risque résiduel et tableau synthèse associé.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
    Requirement("EXI_M5_12", "Documentation des risques résiduels selon le modèle du guide et exportation de la liste correspondante.",
                RequirementCategory.M5_TRAITEMENT, "Atelier 5 – Traitement du risque"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S1 — Identification & Authentification (8)
# ══════════════════════════════════════════════════════
S1_REQUIREMENTS = [
    Requirement("EXI_S1_01", "Compte d'administration dédié distinct des comptes utilisateurs, avec accès exclusif aux interfaces d'administration.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_02", "Le compte administrateur gère les différents profils utilisateurs décrits dans la méthode EBIOS RM.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_03", "Création des profils nominative, non générique, basée sur un identifiant unique individuel.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_04", "Authentification minimale basée sur mot‑de‑passe pour tous les profils.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_05", "Droits en lecture/écriture paramétrables par profil utilisateur et par analyse de risques.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_06", "Granularité des autorisations permettant restriction au niveau d'une analyse, groupe d'analyses ou toutes les analyses.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_07", "Validation d'authentification réalisée par le serveur applicatif ou via annuaire externe.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
    Requirement("EXI_S1_08", "Confidentialité et intégrité assurées pour les informations d'identification et d'authentification.",
                RequirementCategory.S1_AUTH, "Sécurité – Identification & Authentification"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S2 — Confidentialité des données (3)
# ══════════════════════════════════════════════════════
S2_REQUIREMENTS = [
    Requirement("EXI_S2_01", "Confidentialité et intégrité garanties pour les données stockées dans l'application.",
                RequirementCategory.S2_CONFIDENTIALITY, "Sécurité – Confidentialité des données"),
    Requirement("EXI_S2_02", "Confidentialité et intégrité garanties pour les données en transit.",
                RequirementCategory.S2_CONFIDENTIALITY, "Sécurité – Confidentialité des données"),
    Requirement("EXI_S2_03", "Mécanismes sécurisés conformes aux guides ANSSI (TLS, IPSEC ou SSH).",
                RequirementCategory.S2_CONFIDENTIALITY, "Sécurité – Confidentialité des données"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S3 — Journalisation (5)
# ══════════════════════════════════════════════════════
S3_REQUIREMENTS = [
    Requirement("EXI_S3_01", "Mise en œuvre d'une journalisation imputable des actions par chaque profil administrateur et utilisateur.",
                RequirementCategory.S3_LOGGING, "Sécurité – Journalisation"),
    Requirement("EXI_S3_02", "Journalisation des évènements d'identification/authentification (locale ou déportée).",
                RequirementCategory.S3_LOGGING, "Sécurité – Journalisation"),
    Requirement("EXI_S3_03", "Si annuaire externe utilisé, journalisation recommandée dans les CGU/CGU d'usage.",
                RequirementCategory.S3_LOGGING, "Sécurité – Journalisation"),
    Requirement("EXI_S3_04", "Si authentification interne, journaliser au minimum : ouverture/fermeture session, verrouillage compte, gestion comptes, accès analyse, manipulation journaux, évènements applicatifs.",
                RequirementCategory.S3_LOGGING, "Sécurité – Journalisation"),
    Requirement("EXI_S3_05", "Protection des données journalisées incluant génération d'un évènement lors de l'effacement des journaux.",
                RequirementCategory.S3_LOGGING, "Sécurité – Journalisation"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S4 — Revue politiques internes Dev (4)
# ══════════════════════════════════════════════════════
S4_REQUIREMENTS = [
    Requirement("EXI_S4_01", "Présentation des politiques/processus internes relatifs au cloisonnement des environnements de développement.",
                RequirementCategory.S4_DEV, "Revue politiques internes – Développement"),
    Requirement("EXI_S4_02", "Présentation des politiques/processus internes relatifs à la revue/audit du code applicatif.",
                RequirementCategory.S4_DEV, "Revue politiques internes – Développement"),
    Requirement("EXI_S4_03", "Présentation des politiques/processus internes relatifs au contrôle d'innocuité avant livraison.",
                RequirementCategory.S4_DEV, "Revue politiques internes – Développement"),
    Requirement("EXI_S4_04", "Présentation des politiques/processus internes relatifs à la veille sur modules/briques tiers (versions, support, vulnérabilités).",
                RequirementCategory.S4_DEV, "Revue politiques internes – Développement"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S5 — Maintien en conditions de sécurité (6)
# ══════════════════════════════════════════════════════
S5_REQUIREMENTS = [
    Requirement("EXI_S5_01", "Engagements relatifs aux exigences EXI_S5_* clairement spécifiés dans la politique MCS.",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
    Requirement("EXI_S5_02", "Affichage clair des versions mineures/majeures supportées selon OS et plateformes d'intégration.",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
    Requirement("EXI_S5_03", "Précision si politique version diffère entre correctifs fonctionnels (MCO) et correctifs sécurité (MCS).",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
    Requirement("EXI_S5_04", "Notification au CERT‑FR dès connaissance d'une faille/vulnérabilité/incidente et émission d'un avis sécurité.",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
    Requirement("EXI_S5_05", "Engagement sur le délai maximal de correction pour les versions supportées.",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
    Requirement("EXI_S5_06", "Publication d'un avis sécurité aux clients finaux dès diffusion d'un correctif.",
                RequirementCategory.S5_MCS, "Maintien en conditions de sécurité"),
]

# ══════════════════════════════════════════════════════
# SÉCURITÉ S6 — CGU (6 exigences, dont 3 typos corrigées)
# ══════════════════════════════════════════════════════
S6_REQUIREMENTS = [
    Requirement("EXI_S6_01", "Inclusion dans les CGU un encart rappelant les exigences EXI_S6_*.",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
    Requirement("EXI_S6_02", "Mention que l'évaluation porte uniquement sur les aspects fonctionnels vis‑à‑vis de la méthode EBIOS RM.",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
    Requirement("EXI_S6_03", "Précision que le label ne remplace pas les démarches de certification/qualification décrites sur le site ANSSI.",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
    Requirement("EXI_S6_04", "Le label ne garantit en aucun cas la robustesse face à des actions malveillantes.",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
    Requirement("EXI_S6_05", "Recommandation à l'utilisateur d'entreprendre une démarche d'homologation sécuritaire selon l'ANSSI.",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
    Requirement("EXI_S6_06", "Matrice affichant l'état de conformité aux guides/bonnes pratiques ANSSI (exemple fourni).",
                RequirementCategory.S6_CGU, "Conditions générales d'emploi & usage"),
]

# ══════════════════════════════════════════════════════
# EXIGENCES SaaS / SecNumCloud (5 exigences)
# ══════════════════════════════════════════════════════
SNC_REQUIREMENTS = [
    Requirement("EXI_SNC1_01", "L'éditeur utilise un prestataire certifié SecNumCloud présent dans la liste ANSSI.",
                RequirementCategory.SNC1_HOSTING, "Exigences SaaS – Hébergement qualifié SecNumCloud",
                scope=RequirementScope.SAAS_ONLY),
    Requirement("EXI_SNC1_02", "Souscription à une offre IaaS/CaaS/PaaS chez cet hébergeur.",
                RequirementCategory.SNC1_HOSTING, "Exigences SaaS – Hébergement qualifié SecNumCloud",
                scope=RequirementScope.SAAS_ONLY),
    Requirement("EXI_SNC2_01", "Fourniture d'une matrice de conformité au guide ANSSI « Recommandations relatives à l'administration sécurisée… » avec justification des écarts.",
                RequirementCategory.SNC2_ADMIN, "Exigences SaaS – Administration sécurisée",
                scope=RequirementScope.SAAS_ONLY),
    Requirement("EXI_SNC3_01", "Fourniture d'une matrice de conformité aux exigences du chapitre 9.7 du référentiel SecNumCloud (Restriction des accès à l'information).",
                RequirementCategory.SNC3_SEGMENT, "Exigences SaaS – Segmentation client",
                scope=RequirementScope.SAAS_ONLY),
    Requirement("EXI_SNC4_01", "Mise en œuvre du chiffrement complet des éléments hébergés chez le fournisseur SaaS (VMs, données clients).",
                RequirementCategory.SNC4_CRYPTO, "Exigences SaaS – Chiffrement des éléments hébergés",
                scope=RequirementScope.SAAS_ONLY),
]

# ══════════════════════════════════════════════════════
# REGISTRE COMPLET (128 exigences)
# ══════════════════════════════════════════════════════
ALL_REQUIREMENTS: list[Requirement] = (
    M1_REQUIREMENTS   # 23
    + M2_REQUIREMENTS # 10
    + M3_REQUIREMENTS # 28
    + M4_REQUIREMENTS # 18
    + M5_REQUIREMENTS # 12
    + S1_REQUIREMENTS # 8
    + S2_REQUIREMENTS # 3
    + S3_REQUIREMENTS # 5
    + S4_REQUIREMENTS # 4
    + S5_REQUIREMENTS # 6
    + S6_REQUIREMENTS # 6
    + SNC_REQUIREMENTS# 5
)                     # = 128

# Index par référence
REQ_BY_REF: dict[str, Requirement] = {r.ref: r for r in ALL_REQUIREMENTS}

# Exigences optionnelles (à implémenter en v2)
OPTIONAL_REQUIREMENTS = [r for r in ALL_REQUIREMENTS if r.optional]

# Exigences obligatoires (scope != SAAS_ONLY)
MANDATORY_REQUIREMENTS = [
    r for r in ALL_REQUIREMENTS
    if not r.optional and r.scope != RequirementScope.SAAS_ONLY
]

# Stats
STATS = {
    "total": len(ALL_REQUIREMENTS),
    "mandatory": len(MANDATORY_REQUIREMENTS),
    "optional": len(OPTIONAL_REQUIREMENTS),
    "saas_only": len([r for r in ALL_REQUIREMENTS if r.scope == RequirementScope.SAAS_ONLY]),
    "by_category": {
        cat.value: len([r for r in ALL_REQUIREMENTS if r.category == cat])
        for cat in RequirementCategory
    },
}

if __name__ == "__main__":
    import json
    print(f"Total exigences : {STATS['total']}")
    print(f"  Obligatoires  : {STATS['mandatory']}")
    print(f"  Optionnelles  : {STATS['optional']}")
    print(f"  SaaS seulement: {STATS['saas_only']}")
    print("\nPar catégorie :")
    for cat, count in STATS["by_category"].items():
        print(f"  {cat:8s} : {count}")
