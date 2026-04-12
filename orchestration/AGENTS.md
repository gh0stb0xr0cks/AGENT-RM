# AGENTS.md — orchestration/

## Rôle de ce module

Implémenter la couche orchestration LangChain : RAG chain, mémoire de session,
routeur d'ateliers, et validation guard. C'est le "cerveau" du pipeline.

## Architecture des chains (LangChain LCEL)

```
chains/rag_chain.py       → Pipeline principal : retrieval + prompt + LLM
chains/validation_chain.py → Guard post-génération (conformité EBIOS)
chains/atelier_chain.py   → Chain complète par atelier (rag + validation)
```

## Flux de données

```
Requête utilisateur
  → routers/atelier_router.py  (identifie l'atelier actif)
  → routers/step_router.py     (identifie l'étape A/B/C/D)
  → chains/rag_chain.py        (retrieval ChromaDB + prompt assembly)
  → LLM Mistral EBIOS RM      (génération via Ollama)
  → chains/validation_chain.py (guard conformité EBIOS)
  → utils/formatting.py        (formatage sortie finale)
```

## Mémoire de session

```python
# memory/session_memory.py
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(
    k=10,                    # 10 derniers échanges
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# memory/atelier_context.py : persiste les sorties par atelier
# Structure : {"A1": {...}, "A2": {...}, "A3": {...}}
# Utilisé pour la cohérence inter-ateliers
```

## Règles de développement spécifiques

1. Toutes les chains doivent être LCEL (pas les chains legacy LangChain v1)
2. Le paramètre `streaming=True` pour la chain principale (UX)
3. Le guard validation utilise `streaming=False` et `temperature=0.05`
4. Loguer chaque appel LLM dans `data/session_cache/` pour debug
5. La chain de validation ne doit pas modifier la réponse — seulement signaler

## API interne (utils/)

```python
# formatting.py
def format_rag_context(docs: list[Document]) -> str:
    """Formate les chunks RAG avec références de source [Réf.N — SOURCE p.PAGE]"""

# chunk_formatter.py
def format_atelier_output(answer: str, atelier: str) -> dict:
    """Normalise la sortie pour l'affichage et l'export"""
```
