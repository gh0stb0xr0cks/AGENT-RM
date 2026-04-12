"""
rag_chain.py — Pipeline RAG principal (LangChain LCEL)
Orchestre retrieval ChromaDB + assemblage prompt + inférence Mistral EBIOS RM.
"""
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain.memory import ConversationBufferWindowMemory
from langchain.retrievers import EnsembleRetriever, BM25Retriever

from prompts.ateliers import ATELIER_TEMPLATES
from prompts.system.system_prompt import SYSTEM_PROMPT
from orchestration.utils.formatting import format_rag_context
from orchestration.memory.atelier_context import AtelierContext
from inference.configs.ollama_config import OLLAMA_BASE_URL, LLM_MODEL_NAME

RETRIEVAL_K = {"A1": 5, "A2": 6, "A3": 7, "A4": 8, "A5": 6}
SIMILARITY_THRESHOLD = 0.75
HYBRID_WEIGHTS = (0.7, 0.3)


def build_retriever(vectorstore: Chroma, atelier: str, corpus_docs: list):
    """Retriever hybride : sémantique (ChromaDB) + lexical (BM25)."""
    k = RETRIEVAL_K.get(atelier, 6)

    semantic = vectorstore.as_retriever(
        search_type="similarity_score_threshold",
        search_kwargs={
            "k": k,
            "score_threshold": SIMILARITY_THRESHOLD,
            "filter": {
                "$or": [
                    {"atelier": {"$eq": atelier}},
                    {"atelier": {"$eq": "all"}},
                ]
            },
        },
    )
    bm25 = BM25Retriever.from_documents(corpus_docs, k=max(k // 2, 3))
    return EnsembleRetriever(
        retrievers=[semantic, bm25],
        weights=list(HYBRID_WEIGHTS),
    )


def build_ebios_chain(
    atelier: str,
    vectorstore: Chroma,
    corpus_docs: list,
    memory: ConversationBufferWindowMemory,
    atelier_context: AtelierContext,
    temperature: float = 0.2,
):
    """
    Construit la chain LangChain LCEL pour un atelier donné.
    Retourne une chain invocable (streaming activé).
    """
    retriever = build_retriever(vectorstore, atelier, corpus_docs)

    llm = ChatOllama(
        model=LLM_MODEL_NAME,
        base_url=OLLAMA_BASE_URL,
        temperature=temperature,
        num_predict=2048,
        streaming=True,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", ATELIER_TEMPLATES[atelier]),
    ])

    chain = (
        {
            "rag_context": retriever | RunnableLambda(format_rag_context),
            "question": RunnablePassthrough(),
            "chat_history": RunnableLambda(
                lambda _: memory.load_memory_variables({}).get("chat_history", [])
            ),
            "historique_session": RunnableLambda(
                lambda _: atelier_context.format_for_prompt(atelier)
            ),
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    return chain
