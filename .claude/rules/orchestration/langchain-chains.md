---
paths:
  - "orchestration/**/*"
  - "prompts/**/*"
  - "rag/**/*"
---

# Règles orchestration LangChain + RAG + Prompts

## Impératifs LangChain
- Utiliser exclusivement LCEL (pas les chains legacy LangChain v1)
- Chain principale : `streaming=True` (UX fluide)
- Guard validation  : `streaming=False`, `temperature=0.05`
- Loguer chaque appel LLM dans `data/session_cache/` pour debug

## Températures par atelier (NE PAS modifier sans benchmark)
```python
ATELIER_TEMPERATURES = {
    "A1": 0.2,   # Structuration stricte — terminologie normalisée
    "A2": 0.3,   # Légère créativité pour variété des SR/OV
    "A3": 0.4,   # Modélisation adversariale
    "A4": 0.35,  # Modes opératoires techniques
    "A5": 0.2,   # Cohérence stricte avec A1-A4
}
```

## ChromaDB — paramètres retrieval
```python
SIMILARITY_THRESHOLD = 0.75   # Score cosine minimum
HYBRID_WEIGHTS = (0.7, 0.3)  # Sémantique / BM25
RETRIEVAL_K = {"A1":5, "A2":6, "A3":7, "A4":8, "A5":6}
```

## Métadonnées ChromaDB obligatoires sur chaque chunk
atelier · type · source · secteur · etape · page · doc_id

## Mémoire de session
```python
ConversationBufferWindowMemory(k=10, memory_key="chat_history")
# Au-delà de 10 échanges → passer à ConversationSummaryMemory
```

## Variables communes à tous les templates de prompt
system_prompt · rag_context · organisation · secteur · historique_session

## Guard post-génération
- Ne JAMAIS modifier la réponse — seulement signaler les écarts
- Retourner : VALIDÉ · CORRECTION REQUISE · REJET
- Vérifier : terminologie + champs obligatoires + cohérence inter-ateliers
