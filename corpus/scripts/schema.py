"""
schema.py — Schéma de validation du corpus EBIOS RM
Utilisé par tous les scripts de génération et de filtrage.
"""
from dataclasses import dataclass, field
from typing import Literal
from enum import Enum


class Atelier(str, Enum):
    A1 = "A1"
    A2 = "A2"
    A3 = "A3"
    A4 = "A4"
    A5 = "A5"


class Secteur(str, Enum):
    SANTE = "sante"
    INDUSTRIE = "industrie"
    COLLECTIVITE = "collectivite"
    DEFENSE = "defense"
    FINANCE = "finance"
    ENERGIE = "energie"
    ALL = "all"


class ExampleType(str, Enum):
    GUIDE = "guide"           # Extrait documentation ANSSI
    SYNTHETIQUE = "synthetique"  # Exemple généré
    CONTRE_EXEMPLE = "contre_exemple"  # Erreur + correction


@dataclass
class Message:
    role: Literal["system", "user", "assistant"]
    content: str


@dataclass
class CorpusMetadata:
    atelier: Atelier
    etape: Literal["A", "B", "C", "D", "all"]
    secteur: Secteur
    type: ExampleType
    valide_par: str
    qualite: int  # 1-5, minimum 4 pour inclusion train


@dataclass
class CorpusExample:
    messages: list[Message]
    metadata: CorpusMetadata

    def to_dict(self) -> dict:
        return {
            "messages": [
                {"role": m.role, "content": m.content}
                for m in self.messages
            ],
            "metadata": {
                "atelier": self.metadata.atelier.value,
                "etape": self.metadata.etape,
                "secteur": self.metadata.secteur.value,
                "type": self.metadata.type.value,
                "valide_par": self.metadata.valide_par,
                "qualite": self.metadata.qualite,
            }
        }


# Termes EBIOS RM 2024 (requis dans les exemples)
REQUIRED_TERMS = [
    "valeurs métier", "biens supports",
    "événements redoutés", "sources de risque",
    "objectifs visés", "parties prenantes",
]

# Termes EBIOS 2010 INTERDITS (à ne jamais utiliser)
FORBIDDEN_TERMS = [
    "biens essentiels", "actifs critiques", "actifs",
    "menaces principales", "PACS",
    "plan d'amélioration continue de la sécurité",
    "risques cyber", "attaquants",
]

# Échelles officielles EBIOS RM
GRAVITY_SCALE = {
    "G1": "Mineure", "G2": "Significative",
    "G3": "Grave", "G4": "Critique",
}

LIKELIHOOD_SCALE = {
    "V1": "Peu vraisemblable", "V2": "Vraisemblable",
    "V3": "Très vraisemblable", "V4": "Quasi-certain",
}
