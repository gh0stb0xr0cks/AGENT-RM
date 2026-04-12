"""
Fixtures partagées pour les tests EBIOS RM.
"""

import pytest


# ── Exemples EBIOS RM (terminologie 2024 correcte) ──────────────────────────

CORRECT_EBIOS_RESPONSE = """## Atelier 1 — Cadrage et socle de securite

### Valeurs metier identifiees
- Donnees de sante des patients (DLP)
- Continuite du service d'urgences
- Confidentialite des dossiers medicaux

### Biens supports
- Serveur HIS (systeme d'information hospitalier)
- Reseau interne WiFi / filaire
- Poste de travail des soignants

### Evenements redoutes
- Fuite de donnees de sante (Gravite: G4 Critique)
- Indisponibilite du SIH > 4h (Gravite: G3 Grave)
"""

# NOTE: contient volontairement des FORBIDDEN_TERMS EBIOS 2010 pour les tests
INCORRECT_EBIOS_RESPONSE = """## Analyse de risques

### Biens essentiels
- Donnees patient

### Menaces identifiees
- Attaque ransomware
- Fuite de donnees

### Actifs critiques
- Serveur principal
"""


# ── Fixtures de documents RAG ────────────────────────────────────────────────


@pytest.fixture
def sample_rag_documents():
    """Documents simulant des résultats de retrieval ChromaDB."""
    return [
        {
            "page_content": "Les valeurs metier representent les elements essentiels "
            "de l'organisation que la demarche EBIOS RM vise a proteger.",
            "metadata": {
                "source": "ANSSI",
                "page": 15,
                "doc_id": "guide_ebios_rm_2024",
                "atelier": "A1",
                "type": "guide",
            },
        },
        {
            "page_content": "Les sources de risque sont les elements generateurs "
            "de risque, associes a des objectifs vises specifiques.",
            "metadata": {
                "source": "ANSSI",
                "page": 42,
                "doc_id": "guide_ebios_rm_2024",
                "atelier": "A2",
                "type": "guide",
            },
        },
        {
            "page_content": "Le plan de traitement du risque definit les mesures "
            "de securite a mettre en oeuvre pour reduire les risques residuels.",
            "metadata": {
                "source": "ClubEBIOS",
                "page": 8,
                "doc_id": "fiches_methodes",
                "atelier": "A5",
                "type": "fiche",
            },
        },
    ]


@pytest.fixture
def sample_langchain_documents():
    """Documents au format LangChain Document."""

    class MockDocument:
        def __init__(self, page_content, metadata):
            self.page_content = page_content
            self.metadata = metadata

    return [
        MockDocument(
            page_content="Les valeurs metier sont les elements fondamentaux.",
            metadata={"source": "ANSSI", "page": 10, "doc_id": "guide", "atelier": "A1"},
        ),
        MockDocument(
            page_content="Les scenarios de risque strategiques sont definis en A3.",
            metadata={"source": "ANSSI", "page": 55, "doc_id": "guide", "atelier": "A3"},
        ),
    ]


@pytest.fixture
def sample_text_for_chunking():
    """Texte simulant un extrait de PDF EBIOS RM pour tester le chunking."""
    return (
        "La methode EBIOS Risk Manager est structuree en 5 ateliers.\n\n"
        "Atelier 1 : Cadrage et socle de securite\n"
        "L'objectif est de definir le perimetre de l'etude, "
        "identifier les valeurs metier et les biens supports, "
        "puis evaluer les evenements redoutes.\n\n"
        "Atelier 2 : Sources de risque\n"
        "On identifie les sources de risque et leurs objectifs vises. "
        "La cotation de la pertinence de chaque couple SR/OV est realisee "
        "selon l'echelle V1 a V4.\n\n"
        "Atelier 3 : Scenarios strategiques\n"
        "Les parties prenantes de l'ecosysteme sont analysees. "
        "Les scenarios de risque strategiques sont construits "
        "en croisant les sources de risque avec les biens supports "
        "de l'ecosysteme.\n\n"
        "Atelier 4 : Scenarios operationnels\n"
        "Les modes operatoires sont detailles a l'aide de la base "
        "MITRE ATT&CK. Les actions elementaires sont identifiees "
        "et la vraisemblance operationnelle est cotee.\n\n"
        "Atelier 5 : Traitement du risque\n"
        "Le plan de traitement du risque est elabore. "
        "Les mesures de securite sont definies et les risques residuels evalues."
    )


@pytest.fixture
def sample_metadata():
    """Métadonnées type pour un chunk EBIOS RM."""
    return {
        "doc_id": "guide_ebios_rm_2024",
        "atelier": "all",
        "type": "guide",
        "source": "ANSSI",
        "secteur": "all",
        "etape": "all",
        "page": 1,
    }
