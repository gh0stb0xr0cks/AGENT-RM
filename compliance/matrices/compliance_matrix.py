"""
compliance_matrix.py — Matrice de couverture des exigences ANSSI
Lie chaque exigence ANSSI aux modules du projet qui la couvrent.

Rôle : suivi de la progression vers la qualification ANSSI.
Mise à jour : à chaque implémentation d'une nouvelle exigence.
"""

from compliance.matrices.anssi_requirements import (
    ALL_REQUIREMENTS,
    REQ_BY_REF,
    Requirement,
    RequirementScope,
)
from dataclasses import dataclass, field


@dataclass
class CoverageEntry:
    req_ref: str
    status: str  # TODO | IN_PROGRESS | DONE | N/A
    implemented_in: list[str] = field(default_factory=list)
    test_ref: str = ""
    notes: str = ""
    priority: str = "P2"  # P0 (bloquant) | P1 (important) | P2 (normal)


# ══════════════════════════════════════════════════════
# MATRICE DE COUVERTURE
# ══════════════════════════════════════════════════════
# Chaque entrée indique :
#   - status : état d'implémentation
#   - implemented_in : modules/fichiers du projet couvrant l'exigence
#   - test_ref : référence du test automatisé couvrant l'exigence
#   - priority : P0 (bloquant qualification) | P1 | P2
# ══════════════════════════════════════════════════════

COVERAGE: list[CoverageEntry] = [
    # ── ATELIER 1 ─────────────────────────────────────
    # Données de cadrage — gérées via les prompts A1 + modèle de session
    CoverageEntry(
        "EXI_M1_01",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A1_cadrage.py",
            "orchestration/memory/atelier_context.py",
            "orchestration/memory/session_memory.py",
        ],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_01",
        notes="Le LLM génère la structure ; AtelierContext persiste le contexte inter-ateliers ; "
        "l'interface (app/) assure CRUD",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_02",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="CRUD des éléments de cadrage — à implémenter dans l'API",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_03",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="Export PDF/DOCX du cadre de l'étude",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_M1_04",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A1_cadrage.py", "evaluation/benchmarks/ebios_rules.py"],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_04",
        notes="LLM génère la liste des missions ; CRUD manquant dans app/",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_05",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A1_cadrage.py",
            "corpus/scripts/schema.py",
            "evaluation/benchmarks/ebios_rules.py",
        ],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_05",
        notes="Champ 'propriétaire' présent dans schema.py CorpusMetadata",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_06",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A1_cadrage.py", "corpus/scripts/schema.py"],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_06",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_07",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="CRUD du périmètre métier-technique",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_08",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="Import/export avec filtres — endpoint dédié requis",
        priority="P1",
    ),
    CoverageEntry("EXI_M1_09", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    CoverageEntry(
        "EXI_M1_10",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A1_cadrage.py", "evaluation/benchmarks/ebios_rules.py"],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_10",
        notes="Association VM/ER vérifiée dans ebios_rules.py",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_11",
        "IN_PROGRESS",
        implemented_in=["corpus/scripts/schema.py", "evaluation/benchmarks/ebios_rules.py"],
        notes="Échelle G1-G4 définie dans schema.py ; paramétrable via app/",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_12",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A1_cadrage.py",
            "evaluation/benchmarks/atelier_checks.py",
        ],
        test_ref="tests/compliance/test_exi_m1.py::test_M1_12",
        notes="Catégories d'impacts définies dans atelier_checks.py",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_13",
        "IN_PROGRESS",
        implemented_in=["evaluation/benchmarks/ebios_rules.py"],
        notes="Cotation gravité vérifiée automatiquement",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M1_14",
        "TODO",
        implemented_in=["app/api/models.py"],
        notes="Champ justification à ajouter dans le modèle de données",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_M1_15",
        "TODO",
        notes="ER non liés à VM (risques accidentels) — cas particulier A1",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_M1_16",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="Export des ER",
        priority="P1",
    ),
    CoverageEntry("EXI_M1_17", "TODO", implemented_in=["app/api/routes.py"], priority="P1"),
    CoverageEntry("EXI_M1_18", "TODO", priority="P1"),
    CoverageEntry("EXI_M1_19", "TODO", priority="P2"),
    CoverageEntry("EXI_M1_20", "TODO", priority="P1"),
    CoverageEntry("EXI_M1_21", "TODO", priority="P1"),
    CoverageEntry("EXI_M1_22", "TODO", priority="P0"),
    CoverageEntry(
        "EXI_M1_23",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="Export socle de sécurité avec filtres",
        priority="P1",
    ),
    # ── ATELIER 2 ─────────────────────────────────────
    CoverageEntry(
        "EXI_M2_01",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A2_sources.py",
            "evaluation/benchmarks/atelier_checks.py",
        ],
        test_ref="tests/compliance/test_exi_m2.py::test_M2_01",
        notes="Catégories SR/OV génériques présentes dans corpus et prompts",
        priority="P0",
    ),
    CoverageEntry("EXI_M2_02", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    CoverageEntry(
        "EXI_M2_03", "IN_PROGRESS", implemented_in=["prompts/ateliers/A2_sources.py"], priority="P0"
    ),
    CoverageEntry(
        "EXI_M2_04",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A2_sources.py", "evaluation/benchmarks/ebios_rules.py"],
        test_ref="tests/compliance/test_exi_m2.py::test_M2_04",
        notes="Critères motivation/ressources/activité dans le prompt A2",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M2_05",
        "IN_PROGRESS",
        implemented_in=["evaluation/benchmarks/ebios_rules.py"],
        notes="Métrique de pertinence définie",
        priority="P0",
    ),
    CoverageEntry("EXI_M2_06", "TODO", priority="P1"),
    CoverageEntry("EXI_M2_07", "TODO", priority="P1"),
    CoverageEntry(
        "EXI_M2_08",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A2_sources.py"],
        notes="Sélection couples P1/P2 intégrée dans le prompt",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M2_09",
        "TODO",
        implemented_in=["app/ui/components.py"],
        notes="Cartographie radar SR/OV — composant UI à développer",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_M2_10",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A2_sources.py",
            "orchestration/memory/atelier_context.py",
        ],
        test_ref="tests/compliance/test_exi_m2.py::test_M2_10",
        notes="Rapprochement ER/SR-OV via la mémoire inter-ateliers",
        priority="P0",
    ),
    # ── ATELIER 3 ─────────────────────────────────────
    CoverageEntry(
        "EXI_M3_01",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A3_strategique.py"],
        priority="P0",
    ),
    CoverageEntry("EXI_M3_02", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    CoverageEntry("EXI_M3_03", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry(
        "EXI_M3_04",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A3_strategique.py"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M3_05",
        "IN_PROGRESS",
        implemented_in=["evaluation/benchmarks/atelier_checks.py"],
        notes="Dangerosité initiale ET résiduelle dans les checks",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M3_06",
        "IN_PROGRESS",
        implemented_in=[
            "evaluation/benchmarks/ebios_rules.py",
            "prompts/ateliers/A3_strategique.py",
        ],
        test_ref="tests/compliance/test_exi_m3.py::test_M3_06",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M3_07",
        "DONE",
        implemented_in=[
            "corpus/scripts/schema.py",
            "evaluation/benchmarks/ebios_rules.py",
            "prompts/ateliers/A3_strategique.py",
        ],
        test_ref="tests/compliance/test_exi_m3.py::test_M3_07",
        notes="Grille dépendance/pénétration/maturité/confiance implémentée",
        priority="P0",
    ),
    CoverageEntry("EXI_M3_08", "TODO", implemented_in=["app/api/routes.py"], priority="P1"),
    CoverageEntry(
        "EXI_M3_09",
        "DONE",
        implemented_in=[
            "evaluation/benchmarks/ebios_rules.py",
            "prompts/ateliers/A3_strategique.py",
        ],
        test_ref="tests/compliance/test_exi_m3.py::test_M3_09",
        notes="Formule (D×P)/(M×C) implémentée dans ebios_rules.py",
        priority="P0",
    ),
    CoverageEntry("EXI_M3_10", "TODO", priority="P1"),
    CoverageEntry("EXI_M3_11", "TODO", priority="P1"),
    CoverageEntry("EXI_M3_12", "TODO", implemented_in=["app/api/routes.py"], priority="P1"),
    CoverageEntry(
        "EXI_M3_13",
        "TODO",
        implemented_in=["app/ui/components.py"],
        notes="Composant radar à développer",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_M3_14",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A3_strategique.py"],
        notes="PPC identifiées dans le prompt ; distinction visuelle = app/",
        priority="P0",
    ),
    CoverageEntry("EXI_M3_15", "TODO", priority="P0"),
    CoverageEntry(
        "EXI_M3_16",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A3_strategique.py"],
        notes="Cas sans atelier 4 couvert dans le prompt A3",
        priority="P1",
    ),
    CoverageEntry("EXI_M3_17", "TODO", priority="P1"),
    CoverageEntry(
        "EXI_M3_18",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A3_strategique.py",
            "evaluation/benchmarks/atelier_checks.py",
        ],
        test_ref="tests/compliance/test_exi_m3.py::test_M3_18",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M3_19",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A3_strategique.py",
            "orchestration/memory/atelier_context.py",
        ],
        priority="P0",
    ),
    CoverageEntry("EXI_M3_20", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry(
        "EXI_M3_21",
        "DONE",
        implemented_in=["evaluation/benchmarks/ebios_rules.py"],
        test_ref="tests/compliance/test_exi_m3.py::test_M3_21",
        notes="Règle gravité scénario = gravité ER implémentée",
        priority="P0",
    ),
    CoverageEntry("EXI_M3_22", "TODO", priority="P1"),
    CoverageEntry("EXI_M3_23", "TODO", priority="P1"),
    CoverageEntry(
        "EXI_M3_24",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A3_strategique.py"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M3_25",
        "IN_PROGRESS",
        implemented_in=["evaluation/benchmarks/ebios_rules.py"],
        notes="Formule résiduelle = même algorithme que initiale",
        priority="P0",
    ),
    CoverageEntry("EXI_M3_26", "TODO", implemented_in=["app/ui/components.py"], priority="P1"),
    CoverageEntry("EXI_M3_27", "TODO", priority="P0"),
    CoverageEntry("EXI_M3_28", "TODO", priority="P1"),
    # ── ATELIER 4 ─────────────────────────────────────
    CoverageEntry(
        "EXI_M4_01",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A4_operationnel.py",
            "orchestration/memory/atelier_context.py",
        ],
        priority="P0",
    ),
    CoverageEntry("EXI_M4_02", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry(
        "EXI_M4_03",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A4_operationnel.py", "corpus/scripts/schema.py"],
        notes="Catégories AE : CONNAITRE/RENTRER/TROUVER/EXPLOITER",
        priority="P0",
    ),
    CoverageEntry("EXI_M4_04", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry(
        "EXI_M4_05",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A4_operationnel.py"],
        test_ref="tests/compliance/test_exi_m4.py::test_M4_05",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_06",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A4_operationnel.py"],
        notes="Opérateurs ET/OU dans le prompt A4",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_07",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A4_operationnel.py"],
        notes="Sélection méthode expresse/standard/avancée dans le prompt",
        priority="P0",
    ),
    CoverageEntry("EXI_M4_08", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    CoverageEntry(
        "EXI_M4_09",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A4_operationnel.py"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_10",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A4_operationnel.py",
            "evaluation/benchmarks/ebios_rules.py",
        ],
        test_ref="tests/compliance/test_exi_m4.py::test_M4_10",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_11",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A4_operationnel.py",
            "evaluation/benchmarks/ebios_rules.py",
        ],
        test_ref="tests/compliance/test_exi_m4.py::test_M4_11",
        notes="Matrice Pr×Diff implémentée dans ebios_rules.py",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_12",
        "IN_PROGRESS",
        implemented_in=["corpus/scripts/schema.py", "evaluation/benchmarks/ebios_rules.py"],
        notes="Grilles V1-V4 / D1-D4 définies et paramétrables",
        priority="P0",
    ),
    CoverageEntry("EXI_M4_13", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry(
        "EXI_M4_14",
        "IN_PROGRESS",
        implemented_in=[
            "evaluation/benchmarks/ebios_rules.py",
            "prompts/ateliers/A4_operationnel.py",
        ],
        test_ref="tests/compliance/test_exi_m4.py::test_M4_14",
        notes="Algorithmes standard et avancé implémentés",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M4_15",
        "IN_PROGRESS",
        implemented_in=[
            "rag/scripts/build_index.py",
            "rag/scripts/add_documents.py",
            "rag/embeddings/openrouter_embeddings.py",
            "rag/embeddings/chunker.py",
            "rag/embeddings/embedding_config.py",
            "orchestration/chains/rag_chain.py",
            "orchestration/utils/formatting.py",
            "orchestration/memory/atelier_context.py",
        ],
        test_ref="tests/integration/test_rag_chain.py",
        notes="Pipeline RAG complet : chunking token-aware, embeddings multilingual-e5-base, "
        "retrieval hybride (sémantique+BM25), formatage avec références [Réf.N], "
        "contexte inter-ateliers A1→A5. Sources : PDF ANSSI + CSV MITRE + corpus synth.",
        priority="P1",
    ),
    CoverageEntry("EXI_M4_16", "TODO", priority="P1"),
    CoverageEntry("EXI_M4_17", "TODO", implemented_in=["app/ui/components.py"], priority="P1"),
    CoverageEntry("EXI_M4_18", "TODO", priority="P1"),
    # ── ATELIER 5 ─────────────────────────────────────
    CoverageEntry(
        "EXI_M5_01",
        "TODO",
        implemented_in=["app/ui/components.py"],
        notes="Cartographie risque (matrice Gravité×Vraisemblance)",
        priority="P0",
    ),
    CoverageEntry("EXI_M5_02", "TODO", priority="P1"),
    CoverageEntry("EXI_M5_03", "TODO", priority="P2", notes="Optionnel — v2"),
    CoverageEntry("EXI_M5_04", "TODO", implemented_in=["app/ui/components.py"], priority="P1"),
    CoverageEntry(
        "EXI_M5_05",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A5_traitement.py"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_M5_06",
        "IN_PROGRESS",
        implemented_in=[
            "prompts/ateliers/A5_traitement.py",
            "evaluation/benchmarks/atelier_checks.py",
        ],
        test_ref="tests/compliance/test_exi_m5.py::test_M5_06",
        notes="Champs obligatoires plan traitement vérifiés dans checks",
        priority="P0",
    ),
    CoverageEntry("EXI_M5_07", "TODO", priority="P1"),
    CoverageEntry(
        "EXI_M5_08",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A5_traitement.py"],
        priority="P0",
    ),
    CoverageEntry("EXI_M5_09", "TODO", priority="P1"),
    CoverageEntry("EXI_M5_10", "TODO", implemented_in=["app/ui/components.py"], priority="P1"),
    CoverageEntry("EXI_M5_11", "TODO", priority="P1"),
    CoverageEntry(
        "EXI_M5_12",
        "IN_PROGRESS",
        implemented_in=["prompts/ateliers/A5_traitement.py"],
        priority="P0",
    ),
    # ── SÉCURITÉ S1 ───────────────────────────────────
    CoverageEntry(
        "EXI_S1_01",
        "TODO",
        implemented_in=["app/api/dependencies.py"],
        notes="Compte admin dédié — à implémenter dans le système d'auth",
        priority="P0",
    ),
    CoverageEntry("EXI_S1_02", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S1_03", "TODO", implemented_in=["app/api/models.py"], priority="P0"),
    CoverageEntry("EXI_S1_04", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S1_05", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S1_06", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S1_07", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S1_08", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    # ── SÉCURITÉ S2 ───────────────────────────────────
    CoverageEntry(
        "EXI_S2_01",
        "IN_PROGRESS",
        implemented_in=["inference/configs/ollama_config.py"],
        notes="Mode offline = données ne quittent jamais le SI ; chiffrement stockage à formaliser",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S2_02",
        "IN_PROGRESS",
        notes="Mode offline : pas de transit réseau par défaut. En mode SaaS : TLS obligatoire",
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S2_03",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="TLS pour l'API FastAPI locale",
        priority="P0",
    ),
    # ── SÉCURITÉ S3 ───────────────────────────────────
    CoverageEntry(
        "EXI_S3_01",
        "TODO",
        implemented_in=["app/api/routes.py"],
        notes="Journalisation structurée à implémenter dans FastAPI",
        priority="P0",
    ),
    CoverageEntry("EXI_S3_02", "TODO", implemented_in=["app/api/dependencies.py"], priority="P0"),
    CoverageEntry("EXI_S3_03", "TODO", notes="Mention dans CGU", priority="P1"),
    CoverageEntry("EXI_S3_04", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    CoverageEntry("EXI_S3_05", "TODO", implemented_in=["app/api/routes.py"], priority="P0"),
    # ── SÉCURITÉ S4 ───────────────────────────────────
    CoverageEntry(
        "EXI_S4_01",
        "TODO",
        implemented_in=[".github/workflows/ci.yml"],
        notes="Politique de cloisonnement env. dev/test/prod — à documenter",
        priority="P1",
    ),
    CoverageEntry(
        "EXI_S4_02",
        "TODO",
        implemented_in=[".github/workflows/ci.yml"],
        notes="Code review obligatoire via GitHub PR — politique à formaliser",
        priority="P1",
    ),
    CoverageEntry("EXI_S4_03", "TODO", implemented_in=[".github/workflows/ci.yml"], priority="P1"),
    CoverageEntry(
        "EXI_S4_04",
        "TODO",
        implemented_in=[".github/workflows/ci.yml", "pyproject.toml"],
        notes="Dépendance scanning automatique — à configurer en CI",
        priority="P1",
    ),
    # ── SÉCURITÉ S5 ───────────────────────────────────
    CoverageEntry(
        "EXI_S5_01",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S5_02", "TODO", notes="Matrice versions supportées à publier", priority="P1"
    ),
    CoverageEntry("EXI_S5_03", "TODO", priority="P1"),
    CoverageEntry("EXI_S5_04", "TODO", notes="Processus CERT-FR à formaliser", priority="P0"),
    CoverageEntry("EXI_S5_05", "TODO", priority="P0"),
    CoverageEntry("EXI_S5_06", "TODO", priority="P0"),
    # ── SÉCURITÉ S6 ───────────────────────────────────
    CoverageEntry(
        "EXI_S6_01",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P1",
    ),
    CoverageEntry(
        "EXI_S6_02",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S6_03",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S6_04",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P0",
    ),
    CoverageEntry(
        "EXI_S6_05",
        "TODO",
        implemented_in=["compliance/docs/QUALIFICATION_GUIDE.md"],
        priority="P1",
    ),
    CoverageEntry(
        "EXI_S6_06",
        "TODO",
        implemented_in=["compliance/matrices/compliance_matrix.py"],
        notes="Ce fichier IS la matrice de conformité ANSSI demandée",
        priority="P0",
    ),
    # ── SaaS / SecNumCloud ────────────────────────────
    CoverageEntry(
        "EXI_SNC1_01",
        "N/A",
        notes="Mode offline uniquement pour le POC. Exigence applicable uniquement en déploiement SaaS.",
        priority="P2",
    ),
    CoverageEntry("EXI_SNC1_02", "N/A", notes="Idem — SaaS hors scope POC", priority="P2"),
    CoverageEntry("EXI_SNC2_01", "N/A", notes="Idem — SaaS hors scope POC", priority="P2"),
    CoverageEntry("EXI_SNC3_01", "N/A", notes="Idem — SaaS hors scope POC", priority="P2"),
    CoverageEntry("EXI_SNC4_01", "N/A", notes="Idem — SaaS hors scope POC", priority="P2"),
]

# ══════════════════════════════════════════════════════
# API de consultation
# ══════════════════════════════════════════════════════
COVERAGE_BY_REF: dict[str, CoverageEntry] = {e.req_ref: e for e in COVERAGE}


def get_compliance_stats() -> dict:
    """Retourne les statistiques de couverture par statut et priorité."""
    by_status = {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0, "N/A": 0}
    by_priority = {
        "P0": {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0, "N/A": 0},
        "P1": {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0, "N/A": 0},
        "P2": {"TODO": 0, "IN_PROGRESS": 0, "DONE": 0, "N/A": 0},
    }

    for e in COVERAGE:
        by_status[e.status] = by_status.get(e.status, 0) + 1
        by_priority[e.priority][e.status] = by_priority[e.priority].get(e.status, 0) + 1

    total = len(COVERAGE)
    done_or_progress = by_status["DONE"] + by_status["IN_PROGRESS"]
    return {
        "total": total,
        "by_status": by_status,
        "by_priority": by_priority,
        "completion_pct": round(by_status["DONE"] / total * 100, 1),
        "in_scope_pct": round(done_or_progress / total * 100, 1),
        "p0_todo": by_priority["P0"]["TODO"],
        "p0_blocking": by_priority["P0"]["TODO"],
    }


if __name__ == "__main__":
    stats = get_compliance_stats()
    print(f"\n{'═' * 55}")
    print(f"  MATRICE DE CONFORMITÉ ANSSI EBIOS RM")
    print(f"{'═' * 55}")
    print(f"  Total exigences  : {stats['total']}")
    print(f"  DONE             : {stats['by_status']['DONE']}")
    print(f"  IN_PROGRESS      : {stats['by_status']['IN_PROGRESS']}")
    print(f"  TODO             : {stats['by_status']['TODO']}")
    print(f"  N/A (SaaS only)  : {stats['by_status']['N/A']}")
    print(f"  Taux complétion  : {stats['completion_pct']}%")
    print(f"  Exig. P0 restant : {stats['p0_blocking']} (BLOQUANTES qualification)")
    print(f"{'═' * 55}\n")
