"""
03_generate_counterexamples.py — Génération de contre-exemples annotés.

Les contre-exemples sont des réponses délibérément incorrectes avec annotation
de l'erreur. Ils servent à deux usages :
  1. Fine-tuning DPO/RLHF (rejected samples)
  2. Évaluation du garde-fou terminologique

Types d'erreurs simulées :
  - forbidden_term     : utilisation d'un terme interdit (ex: "menaces")
  - wrong_scale        : cotation hors échelle (ex: "niveau 3" au lieu de "G3")
  - wrong_methodology  : confusion avec ISO 27005 ou EBIOS 2010
  - incomplete_answer  : réponse tronquée sans cotation pour A3/A4/A5
  - hallucinated_rule  : invention d'une règle EBIOS RM inexistante

Produit : corpus/raw/synthetics/counterexamples.jsonl

Proportion cible : 1 contre-exemple pour 5 à 7 exemples positifs (ratio --ratio, défaut 6).
Le --count est calculé automatiquement à partir des fichiers positifs existants
dans raw/synthetics/ si non précisé.

Usage :
  python 03_generate_counterexamples.py
  python 03_generate_counterexamples.py --count 200
  python 03_generate_counterexamples.py --ratio 7
  python 03_generate_counterexamples.py --error-type forbidden_term --count 50
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from schema import (
    SCALE_PATTERN,
    SECTORS,
    CorpusExample,
    Message,
)

ROOT = Path(__file__).resolve().parents[1]
SYNTHETICS_DIR = ROOT / "raw" / "synthetics"
SYNTHETICS_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_PATH = SYNTHETICS_DIR / "counterexamples.jsonl"

# Cible théorique par atelier × 14 secteurs (miroir de 02_generate_synthetics.py)
_TARGET_PER_ATELIER: dict[str, int] = {
    "A1": 18, "A2": 22, "A3": 55, "A4": 55, "A5": 28,
}
_THEORETICAL_POSITIVES = sum(_TARGET_PER_ATELIER.values()) * len(SECTORS)


# ---------------------------------------------------------------------------
# Mutations d'erreur (logique inchangée)
# ---------------------------------------------------------------------------

def mutate_forbidden_term(answer: str) -> tuple[str, str]:
    """Remplace un terme ANSSI par son équivalent interdit."""
    replacements = {
        "valeurs métier":            "biens essentiels",
        "biens supports":            "actifs",
        "sources de risque":         "menaces",
        "plan de traitement du risque": "PACS",
        "risque résiduel":           "risque net",
        "risque initial":            "risque brut",
    }
    for correct, wrong in replacements.items():
        if correct in answer:
            mutated = answer.replace(correct, wrong, 1)
            return mutated, "forbidden_term"
    # Fallback : injection directe
    mutated = answer + "\n\nLes menaces identifiées sont prioritaires."
    return mutated, "forbidden_term"


def mutate_wrong_scale(answer: str) -> tuple[str, str]:
    """Remplace une cotation G/V par une notation erronée."""
    mutated = re.sub(r'\bG([1-4])\b', r'niveau \1', answer)
    mutated = re.sub(r'\bV([1-4])\b', r'vraisemblance \1', mutated)
    if mutated == answer:
        mutated = answer + "\n\nLe niveau de risque est estimé à 3/5."
    return mutated, "wrong_scale"


def mutate_wrong_methodology(answer: str) -> tuple[str, str]:
    """Insère une confusion avec ISO 27005 ou EBIOS 2010."""
    confusion_phrases = [
        "\n\nConformément à l'approche ISO 27005, les biens essentiels sont classifiés "
        "selon leur criticité métier.",
        "\n\nSelon EBIOS 2010, les événements redoutés sont cotés de 1 à 4.",
        "\n\nL'analyse des risques résiduels s'appuie sur la matrice EBIOS classique "
        "(vraisemblance × impact).",
        "\n\nLes actifs informationnels sont identifiés conformément à l'ISO/IEC 27001.",
    ]
    mutated = answer + random.choice(confusion_phrases)
    return mutated, "wrong_methodology"


def mutate_incomplete_answer(answer: str) -> tuple[str, str]:
    """Tronque la réponse au premier marqueur G/V (SCALE_PATTERN) ou à mi-chemin."""
    match = SCALE_PATTERN.search(answer)
    if match:
        mutated = answer[:match.start()].rstrip() + "\n\n[À compléter.]"
    else:
        mutated = answer[:len(answer) // 2] + "\n\n[À compléter.]"
    return mutated, "incomplete_answer"


def mutate_hallucinated_rule(answer: str) -> tuple[str, str]:
    """Ajoute une règle EBIOS RM inventée."""
    hallucinations = [
        "\n\nNote : selon l'annexe C de la méthode EBIOS RM, tout scénario "
        "stratégique doit obligatoirement être validé par un tiers certificateur.",
        "\n\nL'ANSSI impose un délai maximum de 30 jours entre l'atelier 3 et "
        "l'atelier 4 pour maintenir la cohérence de l'analyse.",
        "\n\nConformément au guide EBIOS RM 2024, la dangerosité minimale requise "
        "pour qu'une partie prenante soit retenue est de 2,5.",
        "\n\nLe RGS impose que toute analyse EBIOS RM soit conduite par un "
        "prestataire qualifié PASSI de niveau 2 minimum.",
        "\n\nSelon l'article 12 du guide EBIOS RM 2024, chaque atelier doit "
        "faire l'objet d'un compte-rendu signé par le commanditaire dans un "
        "délai de 15 jours ouvrés suivant sa tenue.",
    ]
    mutated = answer + random.choice(hallucinations)
    return mutated, "hallucinated_rule"


MUTATION_FUNCTIONS = {
    "forbidden_term":     mutate_forbidden_term,
    "wrong_scale":        mutate_wrong_scale,
    "wrong_methodology":  mutate_wrong_methodology,
    "incomplete_answer":  mutate_incomplete_answer,
    "hallucinated_rule":  mutate_hallucinated_rule,
}


# ---------------------------------------------------------------------------
# Exemples sources pour mutation — un exemple par secteur, tous ateliers couverts
# 14 secteurs correspondant à SECTOR_CONTEXT de 02_generate_synthetics.py
# ---------------------------------------------------------------------------

BASE_EXAMPLES = [
    # ── sante (A3) ────────────────────────────────────────────────────────────
    {
        "atelier": "A3",
        "secteur": "sante",
        "question": "Construis un scénario stratégique pour un CHU ciblé par ransomware.",
        "answer": (
            "Scénario stratégique SS-01 : Chiffrement du SI hospitalier par ransomware.\n\n"
            "Source de risque : groupe cybercriminel organisé.\n"
            "Objectif visé : extorsion financière via interruption des soins.\n"
            "Valeurs métier ciblées : prise en charge des patients, DPI.\n"
            "Biens supports visés : serveurs applicatifs, PACS, réseau interne.\n"
            "Vraisemblance : V3 — Très vraisemblable.\n"
            "Gravité : G4 — Critique (risque vital pour les patients).\n"
            "Niveau de risque initial : Critique."
        ),
    },
    # ── finance (A2) ──────────────────────────────────────────────────────────
    {
        "atelier": "A2",
        "secteur": "finance",
        "question": "Quelles sources de risque prioriser pour une banque de détail ?",
        "answer": (
            "Les sources de risque prioritaires pour une banque de détail sont :\n\n"
            "SR1 — Cybercriminel organisé / Objectif visé : ransomware ou vol de données.\n"
            "SR2 — Insider malveillant / Objectif visé : fraude interne ou revente de données.\n"
            "SR3 — État étranger hostile / Objectif visé : déstabilisation du système financier.\n\n"
            "La pertinence de chaque source de risque est évaluée au regard des "
            "valeurs métier et biens supports identifiés en atelier 1.\n"
            "Vraisemblance retenue pour SR1 : V3. Gravité : G4 — Critique."
        ),
    },
    # ── energie (A1) ──────────────────────────────────────────────────────────
    {
        "atelier": "A1",
        "secteur": "energie",
        "question": "Identifier les biens supports critiques d'un opérateur de réseau électrique.",
        "answer": (
            "Pour la valeur métier 'distribution électrique', les biens supports critiques sont :\n\n"
            "- Systèmes SCADA de conduite du réseau (EMS/SCADA)\n"
            "- Postes de transformation téléopérés\n"
            "- Réseau de télécommunications de contrôle-commande\n"
            "- Centres de dispatching régionaux\n"
            "- Systèmes de comptage communicant (smart meters)\n\n"
            "Le besoin de sécurité dominant est la Disponibilité (DICP), "
            "toute interruption ayant un impact direct sur la continuité de service.\n"
            "Sources de risque associées : État hostile, prestataire de maintenance OT.\n"
            "Gravité d'un événement redouté de perte de disponibilité : G4 — Critique."
        ),
    },
    # ── administration (A5) ───────────────────────────────────────────────────
    {
        "atelier": "A5",
        "secteur": "administration",
        "question": "Comment structurer le plan de traitement du risque pour un ministère ?",
        "answer": (
            "Le plan de traitement du risque intègre pour chaque scénario retenu :\n\n"
            "1. Stratégie de traitement : réduction, transfert, acceptation ou refus.\n"
            "2. Mesures techniques : segmentation réseau, EDR, chiffrement, MFA.\n"
            "3. Mesures organisationnelles : habilitations, formation, PCA/PRA.\n"
            "4. Risque résiduel après mesures : cotation G/V résiduelle.\n"
            "5. Responsable et échéance de mise en œuvre.\n\n"
            "Le dossier d'homologation compile l'ensemble des risques résiduels "
            "pour décision de l'autorité d'homologation.\n"
            "Vraisemblance résiduelle cible : V1. Gravité résiduelle cible : G2."
        ),
    },
    # ── defense (A2) ──────────────────────────────────────────────────────────
    {
        "atelier": "A2",
        "secteur": "defense",
        "question": "Quelles sources de risque retenir pour un industriel de la BITD ?",
        "answer": (
            "Les sources de risque prioritaires pour un industriel de défense sont :\n\n"
            "SR1 — État étranger hostile (APT) / Objectif visé : espionnage des programmes d'armement.\n"
            "SR2 — Insider avec habilitation / Objectif visé : exfiltration de données classifiées.\n"
            "SR3 — Concurrent étranger / Objectif visé : vol de propriété intellectuelle R&D.\n\n"
            "La dangerosité de chaque source de risque est évaluée selon ses ressources, "
            "capacités et motivations au regard des valeurs métier (conception de systèmes d'armes, "
            "protection du secret) et biens supports exposés (SI Confidentiel Défense, outils CAO/FAO).\n"
            "Vraisemblance retenue pour SR1 : V3. Gravité : G4 — Critique "
            "(atteinte aux intérêts fondamentaux de la Nation)."
        ),
    },
    # ── transport (A3) ────────────────────────────────────────────────────────
    {
        "atelier": "A3",
        "secteur": "transport",
        "question": "Construis un scénario stratégique de sabotage pour un réseau ferroviaire.",
        "answer": (
            "Scénario stratégique SS-01 : Paralysie du réseau ferroviaire par ransomware.\n\n"
            "Source de risque : groupe cybercriminel organisé.\n"
            "Objectif visé : extorsion financière via perturbation du trafic.\n"
            "Valeurs métier ciblées : gestion du trafic, sécurité des passagers.\n"
            "Biens supports visés : systèmes ERTMS, SCADA ferroviaire, "
            "réseau de télécommunication ferroviaire.\n"
            "Vraisemblance : V3 — Très vraisemblable.\n"
            "Gravité : G4 — Critique (risque pour la sécurité physique des voyageurs).\n"
            "Niveau de risque initial : Critique."
        ),
    },
    # ── collectivite (A1) ─────────────────────────────────────────────────────
    {
        "atelier": "A1",
        "secteur": "collectivite",
        "question": "Identifier les biens supports d'une mairie pour ses services numériques aux citoyens.",
        "answer": (
            "Pour la valeur métier 'services numériques aux citoyens', "
            "les biens supports critiques sont :\n\n"
            "- Portail citoyen (dépôt de demandes administratives)\n"
            "- SI RH et paie des agents\n"
            "- SI finance et comptabilité publique\n"
            "- Messagerie institutionnelle\n"
            "- Infrastructure cloud mutualisée (hébergement externalisé)\n\n"
            "Le besoin de sécurité dominant est la Disponibilité et la Confidentialité (DICP). "
            "Toute interruption impacte directement le service public rendu aux citoyens.\n"
            "Sources de risque associées : cybercriminel ransomware, prestataire cloud.\n"
            "Gravité d'un événement redouté d'indisponibilité : G3 — Grave."
        ),
    },
    # ── industrie (A4) ────────────────────────────────────────────────────────
    {
        "atelier": "A4",
        "secteur": "industrie",
        "question": "Détaille le mode opératoire d'une compromission OT via un sous-traitant.",
        "answer": (
            "Mode opératoire — Compromission OT/IT via sous-traitant de maintenance :\n\n"
            "Étape 1 : Reconnaissance (T1590) — cartographie des équipements OT exposés "
            "via interfaces de maintenance distante.\n"
            "Étape 2 : Accès initial (T1195.001) — compromission du VPN de maintenance "
            "du sous-traitant (credential stuffing).\n"
            "Étape 3 : Pivot IT→OT (T1021) — mouvement latéral depuis le réseau IT "
            "vers le SCADA usine via passerelle mal segmentée.\n"
            "Étape 4 : Impact (T0831) — manipulation des automates de ligne de production.\n\n"
            "Valeurs métier ciblées : production industrielle, qualité produit.\n"
            "Biens supports visés : MES, SCADA usine, robots industriels connectés.\n"
            "Vraisemblance : V3. Gravité : G4 — arrêt de production, risque industriel majeur."
        ),
    },
    # ── education (A2) ────────────────────────────────────────────────────────
    {
        "atelier": "A2",
        "secteur": "education",
        "question": "Quelles sources de risque retenir pour une université de recherche ?",
        "answer": (
            "Les sources de risque prioritaires pour une université de recherche sont :\n\n"
            "SR1 — État étranger / Objectif visé : espionnage académique et vol de propriété "
            "intellectuelle (brevets, résultats de recherche sensibles).\n"
            "SR2 — Cybercriminel opportuniste / Objectif visé : ransomware ciblant les données "
            "de recherche et les serveurs de laboratoire.\n"
            "SR3 — Étudiant malveillant / Objectif visé : altération de notes ou accès non "
            "autorisé aux données administratives.\n\n"
            "La pertinence est évaluée au regard des valeurs métier (recherche scientifique, "
            "valorisation des brevets) et biens supports exposés (ENT, serveurs de données).\n"
            "Vraisemblance SR1 : V3 (campus ouvert, collaboration internationale).\n"
            "Gravité : G3 — Grave (perte de propriété intellectuelle irréversible)."
        ),
    },
    # ── assurance (A5) ────────────────────────────────────────────────────────
    {
        "atelier": "A5",
        "secteur": "assurance",
        "question": "Comment structurer le plan de traitement du risque pour un vol massif de données sinistres ?",
        "answer": (
            "Le plan de traitement du risque pour un scénario de vol massif de données sinistres :\n\n"
            "1. Stratégie de traitement : réduction (mesures techniques et organisationnelles).\n"
            "2. Mesures techniques : chiffrement des bases de données sinistres, MFA sur portail "
            "assuré, EDR sur postes, DLP, surveillance des accès privilégiés.\n"
            "3. Mesures organisationnelles : clause RGPD renforcée avec prestataires cloud, "
            "formation DPO, procédure de gestion des incidents de violation de données.\n"
            "4. Risque résiduel après mesures : G2 V2 — Significatif mais maîtrisé.\n"
            "5. Responsable : RSSI. Échéance : 6 mois pour les mesures P0.\n\n"
            "Le dossier d'homologation compile les risques résiduels pour l'autorité d'homologation.\n"
            "Valeurs métier protégées : gestion des sinistres, relation client."
        ),
    },
    # ── telecom (A3) ──────────────────────────────────────────────────────────
    {
        "atelier": "A3",
        "secteur": "telecom",
        "question": "Construis un scénario stratégique d'interception massive pour un opérateur télécom.",
        "answer": (
            "Scénario stratégique SS-01 : Interception massive via compromission du réseau cœur IP/MPLS.\n\n"
            "Source de risque : État hostile (APT étatique, capacités offensives avancées).\n"
            "Objectif visé : interception des communications à des fins de renseignement.\n"
            "Valeurs métier ciblées : infrastructure réseau cœur, fourniture d'accès Internet.\n"
            "Biens supports visés : réseau cœur IP/MPLS, équipements RAN, systèmes OSS/BSS.\n"
            "Vraisemblance : V2 — Vraisemblable (capacités étatiques requises, précédents documentés).\n"
            "Gravité : G4 — Critique (atteinte à la souveraineté nationale, violation massive de la vie privée).\n"
            "Niveau de risque initial : Critique."
        ),
    },
    # ── spatial (A1) ──────────────────────────────────────────────────────────
    {
        "atelier": "A1",
        "secteur": "spatial",
        "question": "Identifier les biens supports critiques d'un opérateur de satellites.",
        "answer": (
            "Pour la valeur métier 'opération de satellites', les biens supports critiques sont :\n\n"
            "- Segment sol de contrôle (mission management system)\n"
            "- Liaisons de télécommande chiffrées (uplink/downlink)\n"
            "- Réseaux de stations sol répartis géographiquement\n"
            "- SI mission et systèmes de traitement des données d'observation\n\n"
            "Le besoin de sécurité dominant est la Disponibilité et l'Intégrité (DICP). "
            "Toute compromission des télécommandes peut entraîner la perte définitive du satellite.\n"
            "Sources de risque associées : État hostile (brouillage, spoofing), APT.\n"
            "Gravité d'un événement redouté de perte de contrôle du satellite : G4 — Critique."
        ),
    },
    # ── eau (A3) ──────────────────────────────────────────────────────────────
    {
        "atelier": "A3",
        "secteur": "eau",
        "question": "Construis un scénario stratégique de sabotage pour un service d'eau potable.",
        "answer": (
            "Scénario stratégique SS-01 : Manipulation des automates de chloration par un hacktiviste.\n\n"
            "Source de risque : hacktiviste avec objectif d'atteinte à la santé publique.\n"
            "Objectif visé : altération de la qualité de l'eau potable distribuée.\n"
            "Valeurs métier ciblées : production et distribution d'eau potable, "
            "surveillance qualité de l'eau.\n"
            "Biens supports visés : automates de chloration, SCADA stations de pompage, "
            "capteurs qualité réseau.\n"
            "Vraisemblance : V2 — Vraisemblable (systèmes OT vieillissants, faible cloisonnement).\n"
            "Gravité : G4 — Critique (risque sanitaire direct pour la population).\n"
            "Niveau de risque initial : Critique."
        ),
    },
    # ── alimentaire (A4) ──────────────────────────────────────────────────────
    {
        "atelier": "A4",
        "secteur": "alimentaire",
        "question": "Détaille le mode opératoire d'un ransomware OT ciblant une usine agroalimentaire.",
        "answer": (
            "Mode opératoire — Ransomware OT ciblant la ligne de production agroalimentaire :\n\n"
            "Étape 1 : Accès initial (T1190) — exploitation d'une interface web exposée "
            "sur l'ERP agroalimentaire (patch manquant).\n"
            "Étape 2 : Persistance (T1053) — installation d'une tâche planifiée sur le serveur ERP.\n"
            "Étape 3 : Mouvement latéral (T1021) — pivot depuis le réseau IT vers le réseau OT "
            "via passerelle de supervision mal segmentée.\n"
            "Étape 4 : Impact (T1486) — chiffrement des automates de ligne de production.\n\n"
            "Valeurs métier ciblées : production alimentaire, chaîne du froid.\n"
            "Biens supports visés : automates de ligne de production, système de traçabilité.\n"
            "Vraisemblance : V3. Gravité : G3 — perturbation grave de la chaîne alimentaire, "
            "risque sanitaire potentiel."
        ),
    },
]

# Validation : tous les secteurs de SECTORS doivent être représentés
_SECTORS_IN_BASE = {ex["secteur"] for ex in BASE_EXAMPLES}
_MISSING = set(SECTORS) - _SECTORS_IN_BASE
if _MISSING:
    raise RuntimeError(
        f"BASE_EXAMPLES manque les secteurs suivants : {sorted(_MISSING)}\n"
        f"Ajouter un exemple pour chaque secteur manquant."
    )


# ---------------------------------------------------------------------------
# Calcul automatique du nombre de contre-exemples
# ---------------------------------------------------------------------------

def count_positives() -> int:
    """
    Compte les exemples positifs existants dans raw/synthetics/*.jsonl
    (exclut counterexamples.jsonl lui-même).
    Retourne la valeur théorique si aucun fichier n'existe encore.
    """
    total = 0
    for path in SYNTHETICS_DIR.glob("*.jsonl"):
        if path.name == OUTPUT_PATH.name:
            continue
        try:
            with open(path, encoding="utf-8") as f:
                total += sum(1 for line in f if line.strip())
        except OSError:
            pass
    return total if total > 0 else _THEORETICAL_POSITIVES


# ---------------------------------------------------------------------------
# Génération des contre-exemples
# ---------------------------------------------------------------------------

def generate_counterexample(
    base: dict,
    error_type: str,
    index: int,
) -> CorpusExample:
    """Applique une mutation d'erreur sur un exemple de base (AGENTS.md §4.3)."""
    mutate_fn = MUTATION_FUNCTIONS[error_type]
    mutated_answer, confirmed_type = mutate_fn(base["answer"])

    atelier = base["atelier"]
    secteur = base["secteur"]
    parent_id = base.get("id", f"{atelier.lower()}_{secteur}_base")
    example_id = f"{atelier.lower()}_{secteur}_ce{index:04d}"

    return CorpusExample(
        id=example_id,
        atelier=atelier,
        secteur=secteur,
        source="counterexample",
        is_counterexample=True,
        error_type=confirmed_type,
        messages=[
            Message(role="user",      content=base["question"]),
            Message(role="assistant", content=mutated_answer),
        ],
        metadata={
            # Champs requis §3.3 Volet 3
            "source_chunk":      None,
            "parent_id":         parent_id,
            "mutation_strategy": confirmed_type,
            "word_count":        len(mutated_answer.split()),
            "has_gv_scale":      bool(SCALE_PATTERN.search(mutated_answer)),
        },
    )


def main():
    parser = argparse.ArgumentParser(
        description="Génération de contre-exemples EBIOS RM"
    )
    parser.add_argument(
        "--count", type=int, default=None,
        help=(
            "Nombre total de contre-exemples à générer. "
            "Par défaut : calculé automatiquement depuis les fichiers positifs "
            "existants avec le ratio --ratio."
        ),
    )
    parser.add_argument(
        "--ratio", type=int, default=6,
        choices=range(5, 8), metavar="{5,6,7}",
        help=(
            "Ratio positifs / contre-exemples (défaut : 6). "
            "Doit être entre 5 et 7 pour respecter la proportion cible du corpus."
        ),
    )
    parser.add_argument("--error-type",
                        choices=list(MUTATION_FUNCTIONS.keys()) + ["all"],
                        default="all")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    random.seed(args.seed)

    # Calcul du count cible
    if args.count is None:
        n_positives = count_positives()
        target_count = max(len(BASE_EXAMPLES), n_positives // args.ratio)
        print(
            f"Positifs détectés : {n_positives}  |  "
            f"Ratio 1:{args.ratio}  |  Cible : {target_count} contre-exemples"
        )
    else:
        target_count = args.count
        print(f"Cible (manuel) : {target_count} contre-exemples")

    error_types = (
        list(MUTATION_FUNCTIONS.keys())
        if args.error_type == "all"
        else [args.error_type]
    )

    # Répartition équilibrée entre types d'erreur
    per_type = max(1, target_count // len(error_types))
    examples: list[CorpusExample] = []

    global_idx = 0
    for error_type in error_types:
        for i in range(per_type):
            # Cycle sur tous les secteurs de BASE_EXAMPLES (14 entrées)
            base = BASE_EXAMPLES[i % len(BASE_EXAMPLES)]
            ex = generate_counterexample(base, error_type, global_idx)
            examples.append(ex)
            global_idx += 1
            print(f"  [{error_type}] [{base['secteur']:15s}] {ex.id} ✓")

    # Sauvegarde
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for ex in examples:
            f.write(json.dumps(ex.to_dict(), ensure_ascii=False) + "\n")

    print(f"\n{len(examples)} contre-exemples → {OUTPUT_PATH}")

    # Statistiques par type d'erreur
    from collections import Counter
    counts_type = Counter(ex.error_type for ex in examples)
    print("\nPar type d'erreur :")
    for etype, n in sorted(counts_type.items()):
        print(f"  {etype:25s} : {n}")

    # Statistiques par secteur
    counts_sector = Counter(ex.secteur for ex in examples)
    print("\nPar secteur :")
    for sector in SECTORS:
        n = counts_sector.get(sector, 0)
        print(f"  {sector:15s} : {n}")

    # Vérification de la proportion
    n_pos = count_positives()
    if n_pos > 0:
        actual_ratio = round(n_pos / len(examples), 1)
        in_range = "✓" if 5 <= actual_ratio <= 7 else "⚠ hors cible [5–7]"
        print(f"\nProportions : {n_pos} positifs / {len(examples)} contre-exemples "
              f"= ratio 1:{actual_ratio}  {in_range}")


if __name__ == "__main__":
    main()
