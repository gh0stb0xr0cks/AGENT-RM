"""
session_memory.py — Configuration de la mémoire de session LangChain.

Gère les 10 derniers échanges par session via ConversationBufferWindowMemory.
Conformément à orchestration/AGENTS.md.
"""

import logging
from typing import Optional

from langchain.memory import ConversationBufferWindowMemory

logger = logging.getLogger(__name__)

# Nombre d'échanges conservés en mémoire
MEMORY_WINDOW_K: int = 10


def create_session_memory(
    k: int = MEMORY_WINDOW_K,
    memory_key: str = "chat_history",
    return_messages: bool = True,
) -> ConversationBufferWindowMemory:
    """Crée une instance de mémoire de session.

    Args:
        k: Nombre d'échanges à conserver (fenêtre glissante).
        memory_key: Clé pour accéder à l'historique dans le prompt.
        return_messages: Si True, retourne des Messages LangChain.

    Returns:
        Instance ConversationBufferWindowMemory configurée.
    """
    memory = ConversationBufferWindowMemory(
        k=k,
        memory_key=memory_key,
        return_messages=return_messages,
        output_key="answer",
    )
    logger.debug("Memoire de session creee (k=%d)", k)
    return memory


def get_chat_history(memory: ConversationBufferWindowMemory) -> list:
    """Extrait l'historique de chat depuis la mémoire.

    Args:
        memory: Instance de mémoire de session.

    Returns:
        Liste de messages LangChain ou chaînes vides.
    """
    variables = memory.load_memory_variables({})
    return variables.get("chat_history", [])


def save_interaction(
    memory: ConversationBufferWindowMemory,
    user_input: str,
    ai_output: str,
) -> None:
    """Sauvegarde un échange utilisateur/IA dans la mémoire.

    Args:
        memory: Instance de mémoire de session.
        user_input: Message de l'utilisateur.
        ai_output: Réponse de l'IA.
    """
    memory.save_context(
        {"input": user_input},
        {"answer": ai_output},
    )
    logger.debug("Interaction sauvegardee dans la memoire")
