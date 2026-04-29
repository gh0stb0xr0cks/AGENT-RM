"""
Tests d'intégration pour le pipeline RAG EBIOS RM.
Couvre :
- Retrieval ChromaDB + assemblage prompt
- Formatage du contexte RAG
- Cohérence du contexte inter-ateliers (AtelierContext)
- Validation des métadonnées de chunks

Ces tests utilisent des mocks pour ChromaDB et le LLM (pas de GPU requis).
"""

import sys
import tempfile
from pathlib import Path

import pytest

# Assurer l'accès au projet racine
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.memory.atelier_context import (
    ATELIER_KEYS,
    ATELIER_ORDER,
    AtelierContext,
)
from orchestration.utils.chunk_formatter import format_atelier_output
from orchestration.utils.formatting import format_rag_context
from rag.embeddings.chunker import chunk_text, chunk_text_by_pages
from rag.embeddings.embedding_config import (
    ATELIER_VALUES,
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    EMBEDDING_DIM,
    METADATA_SCHEMA,
    RETRIEVAL_K,
    SIMILARITY_THRESHOLD,
    SOURCE_VALUES,
    TYPE_VALUES,
)

# ═══════════════════════════════════════════════════════════════════════════════
# Tests de la configuration RAG
# ═══════════════════════════════════════════════════════════════════════════════


class TestRagConfiguration:
    """Vérifie que la configuration RAG est conforme au référentiel AGENTS.md."""

    def test_embedding_model_default_is_multilingual_e5(self):
        """AGENTS.md spec : la valeur par défaut est intfloat/multilingual-e5-base.

        Note: la variable d'environnement OPENROUTER_EMBED_MODEL peut surcharger
        cette valeur au runtime. Ce test vérifie la valeur codée dans le source.
        """
        import inspect

        from rag.embeddings import embedding_config

        source = inspect.getsource(embedding_config)
        assert "intfloat/multilingual-e5-base" in source, (
            "La valeur par defaut du modele dans embedding_config.py "
            "doit etre intfloat/multilingual-e5-base"
        )

    def test_embedding_dim_768(self):
        """AGENTS.md spec : EMBEDDING_DIM = 768."""
        assert EMBEDDING_DIM == 768

    def test_chunk_size_512_tokens(self):
        """AGENTS.md spec : CHUNK_SIZE = 512 tokens."""
        assert CHUNK_SIZE == 512

    def test_chunk_overlap_64_tokens(self):
        """AGENTS.md spec : CHUNK_OVERLAP = 64 tokens."""
        assert CHUNK_OVERLAP == 64

    def test_retrieval_k_per_atelier(self):
        """AGENTS.md spec : K par atelier (A1=5, A2=6, A3=7, A4=8, A5=6)."""
        assert RETRIEVAL_K == {
            "A1": 5,
            "A2": 6,
            "A3": 7,
            "A4": 8,
            "A5": 6,
        }

    def test_similarity_threshold(self):
        """AGENTS.md spec : SIMILARITY_THRESHOLD = 0.75."""
        assert SIMILARITY_THRESHOLD == 0.75

    def test_metadata_schema_fields(self):
        """AGENTS.md spec : 7 champs obligatoires dans les métadonnées."""
        required_fields = {"atelier", "type", "source", "secteur", "etape", "page", "doc_id"}
        assert set(METADATA_SCHEMA.keys()) == required_fields

    def test_atelier_values_complete(self):
        assert ATELIER_VALUES == ["A1", "A2", "A3", "A4", "A5", "all"]

    def test_source_values_complete(self):
        assert SOURCE_VALUES == ["ANSSI", "ClubEBIOS", "MITRE", "synth"]

    def test_type_values_complete(self):
        assert TYPE_VALUES == ["guide", "fiche", "exemple", "threat", "matrice"]


# ═══════════════════════════════════════════════════════════════════════════════
# Tests du pipeline RAG (retrieval -> format -> prompt)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRagPipeline:
    """Tests d'intégration du pipeline retrieval -> formatage -> prompt."""

    def test_retrieval_to_format_pipeline(self, sample_rag_documents):
        """Le pipeline complet retrieval -> format doit produire un contexte valide."""
        context = format_rag_context(sample_rag_documents)

        # Le contexte doit contenir des références numérotées
        assert "[Ref.1" in context
        assert "ANSSI" in context

        # Le contexte ne doit pas être vide
        assert len(context) > 50

    def test_format_to_atelier_output(self):
        """Le formatage de sortie d'atelier doit structurer la réponse."""
        answer = (
            "## Valeurs metier\n"
            "- Donnees de sante des patients\n"
            "- Continuite du service d'urgences\n\n"
            "## Biens supports\n"
            "- Serveur HIS\n"
            "- Reseau interne\n"
        )
        output = format_atelier_output(answer, "A1")

        assert output["atelier"] == "A1"
        assert len(output["sections"]) == 2
        assert output["sections"][0]["title"] == "Valeurs metier"
        assert "structured" in output
        assert len(output["structured"]["items"]) == 4

    def test_chunking_to_metadata_pipeline(self, sample_metadata):
        """Les chunks produits doivent avoir des métadonnées conformes au schéma."""
        text = (
            "Les valeurs metier representent les elements fondamentaux "
            "que l'organisation cherche a proteger dans le cadre "
            "de la methode EBIOS Risk Manager."
        )
        chunks = chunk_text(text, sample_metadata)

        for chunk_content, meta in chunks:
            # Vérifier la présence des champs obligatoires
            for field in METADATA_SCHEMA.keys():
                if field != "page":  # page peut ne pas être dans metadata de base
                    assert field in meta, f"Champ '{field}' manquant dans les metadonnees"

            # Vérifier les types
            assert isinstance(meta.get("doc_id", ""), str)
            assert meta["atelier"] in ATELIER_VALUES
            assert meta["source"] in SOURCE_VALUES

    def test_pdf_pages_to_chunks_pipeline(self, sample_metadata):
        """Le chunking par pages doit préserver les numéros de page réels."""
        pages = [
            ("Contenu de la page 15 du guide EBIOS RM.", 15),
            ("Contenu de la page 16 avec les sources de risque.", 16),
        ]
        chunks = chunk_text_by_pages(pages, sample_metadata)

        page_numbers = [meta["page"] for _, meta in chunks]
        assert all(p in [15, 16] for p in page_numbers)


# ═══════════════════════════════════════════════════════════════════════════════
# Tests AtelierContext (cohérence inter-ateliers)
# ═══════════════════════════════════════════════════════════════════════════════


class TestAtelierContext:
    """Tests d'intégration pour la persistance du contexte inter-ateliers."""

    def test_create_empty_context(self):
        ctx = AtelierContext()
        for atelier in ATELIER_ORDER:
            assert ctx.get(atelier) == {}

    def test_update_and_retrieve(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["Donnees patients", "Continuite service"])
        result = ctx.get("A1", "valeurs_metier")
        assert result == ["Donnees patients", "Continuite service"]

    def test_update_atelier_batch(self):
        ctx = AtelierContext()
        data = {
            "sources_risque": ["Attaquant etatique", "Cybercriminel"],
            "objectifs_vises": ["Exfiltration donnees", "Sabotage"],
        }
        ctx.update_atelier("A2", data)
        assert ctx.get("A2", "sources_risque") == ["Attaquant etatique", "Cybercriminel"]
        assert ctx.get("A2", "objectifs_vises") == ["Exfiltration donnees", "Sabotage"]

    def test_invalid_atelier_raises(self):
        ctx = AtelierContext()
        with pytest.raises(ValueError, match="Atelier invalide"):
            ctx.update("A6", "key", "value")

    def test_previous_context_excludes_current(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM1", "VM2"])
        ctx.update("A2", "sources_risque", ["SR1"])

        previous = ctx.get_previous_context("A3")
        assert "A1" in previous
        assert "A2" in previous
        assert "A3" not in previous

    def test_previous_context_empty_for_a1(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM1"])
        assert ctx.get_previous_context("A1") == {}

    def test_format_for_prompt(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["Donnees patients"])
        ctx.update("A1", "biens_supports", ["Serveur HIS"])

        prompt_text = ctx.format_for_prompt("A2")
        assert "A1" in prompt_text
        assert "valeurs_metier" in prompt_text
        assert "Donnees patients" in prompt_text
        assert "biens_supports" in prompt_text

    def test_format_for_prompt_empty_if_no_previous(self):
        ctx = AtelierContext()
        assert ctx.format_for_prompt("A1") == ""

    def test_completion_status(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM"])
        ctx.update("A1", "biens_supports", ["BS"])

        status = ctx.completion_status()
        assert "A1" in status
        assert "valeurs_metier" in status["A1"]["keys_present"]
        assert "biens_supports" in status["A1"]["keys_present"]
        # Il manque perimetre, evenements_redoutes, echelle_gravite
        assert len(status["A1"]["keys_missing"]) > 0
        assert status["A1"]["complete"] is False

    def test_full_completion(self):
        ctx = AtelierContext()
        for key in ATELIER_KEYS["A1"]:
            ctx.update("A1", key, ["test"])
        assert ctx.is_complete("A1") is True

    def test_reset_single_atelier(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM"])
        ctx.update("A2", "sources_risque", ["SR"])
        ctx.reset("A1")

        assert ctx.get("A1") == {}
        assert ctx.get("A2", "sources_risque") == ["SR"]

    def test_reset_all(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM"])
        ctx.update("A2", "sources_risque", ["SR"])
        ctx.reset()

        for atelier in ATELIER_ORDER:
            assert ctx.get(atelier) == {}

    def test_save_and_load(self):
        """Test de sérialisation/désérialisation JSON."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ctx = AtelierContext(session_dir=tmpdir)
            ctx.update("A1", "valeurs_metier", ["Donnees patients"])
            ctx.update("A2", "sources_risque", ["Attaquant etatique"])

            # Vérifier que le fichier existe
            filepath = Path(tmpdir) / "atelier_context.json"
            assert filepath.exists()

            # Charger et vérifier
            loaded = AtelierContext.load(tmpdir)
            assert loaded.get("A1", "valeurs_metier") == ["Donnees patients"]
            assert loaded.get("A2", "sources_risque") == ["Attaquant etatique"]

    def test_to_dict(self):
        ctx = AtelierContext()
        ctx.update("A1", "valeurs_metier", ["VM1"])
        data = ctx.to_dict()
        assert "context" in data
        assert "timestamps" in data
        assert data["context"]["A1"]["valeurs_metier"] == ["VM1"]


# ═══════════════════════════════════════════════════════════════════════════════
# Tests de cohérence inter-ateliers (scénario end-to-end mocké)
# ═══════════════════════════════════════════════════════════════════════════════


class TestInterAtelierCoherence:
    """Vérifie que les sorties d'un atelier peuvent alimenter le suivant."""

    def test_a1_output_feeds_a2_context(self):
        """Les valeurs métier de A1 doivent apparaitre dans le contexte de A2."""
        ctx = AtelierContext()

        # Simuler la sortie de A1
        format_atelier_output(
            "## Valeurs metier\n- Donnees de sante\n- Continuite service\n"
            "## Biens supports\n- Serveur HIS\n- Reseau WiFi",
            "A1",
        )
        ctx.update_atelier(
            "A1",
            {
                "valeurs_metier": ["Donnees de sante", "Continuite service"],
                "biens_supports": ["Serveur HIS", "Reseau WiFi"],
            },
        )

        # Vérifier le contexte injecté dans A2
        prompt_context = ctx.format_for_prompt("A2")
        assert "Donnees de sante" in prompt_context
        assert "Serveur HIS" in prompt_context

    def test_full_session_flow(self):
        """Simulation d'une session complète A1->A5."""
        ctx = AtelierContext()

        # A1
        ctx.update_atelier(
            "A1",
            {
                "valeurs_metier": ["Donnees patients", "Continuite SIH"],
                "biens_supports": ["Serveur HIS", "Reseau interne"],
            },
        )

        # A2 - utilise le contexte de A1
        a2_context = ctx.format_for_prompt("A2")
        assert "Donnees patients" in a2_context
        ctx.update_atelier(
            "A2",
            {
                "sources_risque": ["Attaquant etatique", "Cybercriminel organise"],
                "objectifs_vises": ["Exfiltration donnees medicales"],
            },
        )

        # A3 - utilise le contexte de A1+A2
        a3_context = ctx.format_for_prompt("A3")
        assert "Donnees patients" in a3_context
        assert "Attaquant etatique" in a3_context
        ctx.update_atelier(
            "A3",
            {
                "scenarios_strategiques": ["Exfiltration via prestataire compromis"],
            },
        )

        # A4 - utilise A1+A2+A3
        a4_context = ctx.format_for_prompt("A4")
        assert "Exfiltration via prestataire" in a4_context
        ctx.update_atelier(
            "A4",
            {
                "scenarios_operationnels": ["Phishing cible -> lateral movement -> exfiltration"],
            },
        )

        # A5 - utilise A1+A2+A3+A4
        a5_context = ctx.format_for_prompt("A5")
        assert "Phishing cible" in a5_context
        assert "Donnees patients" in a5_context
        ctx.update_atelier(
            "A5",
            {
                "plan_traitement": ["Mise en place MFA", "Segmentation reseau"],
            },
        )

        # Vérifier l'état final
        status = ctx.completion_status()
        for atelier in ATELIER_ORDER:
            assert len(status[atelier]["keys_present"]) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# Tests de la terminologie EBIOS RM 2024
# ═══════════════════════════════════════════════════════════════════════════════


class TestEbiosTerminology:
    """Vérifie qu'aucun terme EBIOS 2010 n'est utilisé dans les constantes."""

    FORBIDDEN_TERMS = [
        "biens essentiels",
        "actifs",
        "PACS",
        "risques cyber",
    ]

    def test_atelier_keys_no_forbidden_terms(self):
        """Les clés ATELIER_KEYS ne doivent pas utiliser la terminologie EBIOS 2010."""
        all_keys = []
        for keys in ATELIER_KEYS.values():
            all_keys.extend(keys)

        all_keys_str = " ".join(all_keys).lower()
        for term in self.FORBIDDEN_TERMS:
            assert term.lower() not in all_keys_str, (
                f"Terme EBIOS 2010 interdit '{term}' trouve dans ATELIER_KEYS"
            )

    def test_test_queries_no_forbidden_terms(self):
        """Les requêtes de test ne doivent pas utiliser la terminologie EBIOS 2010."""
        from rag.scripts.test_retrieval import TEST_QUERIES

        all_queries = []
        for queries in TEST_QUERIES.values():
            all_queries.extend(queries)

        all_queries_str = " ".join(all_queries).lower()
        # "menaces" seul est interdit, mais "menace" dans un contexte
        # composé comme "source de menace" pourrait être acceptable
        for term in ["biens essentiels", "PACS", "risques cyber"]:
            assert term.lower() not in all_queries_str, (
                f"Terme EBIOS 2010 interdit '{term}' dans TEST_QUERIES"
            )
