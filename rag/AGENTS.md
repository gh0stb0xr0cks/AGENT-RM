# AGENTS.md — rag/

## Rôle de ce module

Construire et maintenir la base vectorielle ChromaDB locale contenant les
~1 800 chunks du corpus documentaire EBIOS RM pour le système RAG.

## Composants

```
scripts/build_index.py    → Indexation complète du corpus documentaire
scripts/add_documents.py  → Ajout incrémental de nouveaux documents
scripts/test_retrieval.py → Vérification de la qualité du retrieval
scripts/inspect_chunks.py → Debug : visualise les chunks indexés
embeddings/embedding_config.py → Config OpenRouter embeddings
collections/              → Base ChromaDB persistante (~350 Mo)
```

## Modèle d'embedding retenu

```python
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"   # OpenRouter
EMBEDDING_DIM = 768
MAX_CONTEXT = 512   # tokens
```

## Paramètres de chunking

```python
CHUNK_SIZE = 512       # tokens (~380 mots)
CHUNK_OVERLAP = 64     # continuité inter-chunks (listes EBIOS)
SEPARATORS = ["\n\n", "\n", ".", " "]  # respect frontières paragraphes
```

## Schéma de métadonnées ChromaDB

Chaque chunk DOIT avoir ces métadonnées pour le filtrage par atelier :

```python
{
    "atelier":  "A1"|"A2"|"A3"|"A4"|"A5"|"all",
    "type":     "guide"|"fiche"|"exemple"|"threat"|"matrice",
    "source":   "ANSSI"|"ClubEBIOS"|"MITRE"|"synth",
    "secteur":  "sante"|"industrie"|"collectivite"|"all",
    "etape":    "A"|"B"|"C"|"D"|"all",
    "page":     int,    # numéro de page source (traçabilité)
    "doc_id":   str     # identifiant document source
}
```

## Paramètres de retrieval par atelier

```python
RETRIEVAL_K = {
    "A1": 5,   # Termes précis, chunks courts suffisants
    "A2": 6,   # Profils SR/OV + cartographie menaces
    "A3": 7,   # Scénarios stratégiques + écosystème
    "A4": 8,   # Modes opératoires + MITRE ATT&CK
    "A5": 6,   # Plan traitement + exemples mesures
}

SIMILARITY_THRESHOLD = 0.75  # Cosine similarity minimale
HYBRID_ALPHA = 0.25  # Pondération: 0.25 * semantic + 0.75 * BM25
```

## Sources à indexer (docs/ → collections/)

1. `docs/ebios/guide_ebios_rm_2024.pdf`    → atelier=all, source=ANSSI
2. `docs/ebios/fiches_methodes.pdf`        → atelier=all, source=ANSSI
3. `docs/ebios/matrice_rapport_sortie.pdf` → atelier=all, source=ClubEBIOS
4. MITRE ATT&CK subset FR                 → atelier=A4, source=MITRE
5. Corpus synthétique exemples             → atelier=*, source=synth

## Commande de reconstruction complète

```bash
make build-rag
# Équivalent : python rag/scripts/build_index.py --reset --all-sources
```
