"""
Memory tools for Agente_Perfilamiento agents.

This module provides tools for accessing and managing conversation memory
within the agent ecosystem.
"""

from typing import Any, Dict, List

from langchain_core.tools import tool

from agente_perfilamiento.infrastructure.logging.logger import get_logger
from agente_perfilamiento.domain.services.long_term_memory_service import (
    LongTermMemoryService,
)
from agente_perfilamiento.adapters.file_long_term_repository import (
    FileLongTermMemoryRepository,
)
from agente_perfilamiento.infrastructure.persistence.provider import get_memory_service

logger = get_logger(__name__)


@tool
def get_conversation_memory(
    user_id: str,
    agent_name: str = "perfilamiento_agent",
    session_id: str | None = None,
) -> str:
    """
    Retrieve short-term conversation memory window for a specific session/agent.

    Args:
        user_id: The unique identifier for the user (for logging/trace)
        agent_name: Agent name whose window to read
        session_id: Conversation/session identifier

    Returns:
        str: Recent window formatted as text, or notice if empty
    """
    logger.info(f"Retrieving conversation memory for user: {user_id}")

    try:
        if not session_id:
            return "Sin memoria de sesión disponible."
        window = get_memory_service().get_window(
            agent_name=agent_name, session_id=session_id
        )
        if not window:
            return "Sin información previa disponible."
        formatted = []
        for item in window:
            role = item.get("role", "?")
            content = item.get("content", "")
            formatted.append(f"{role}: {content}")
        return "\n".join(formatted)

    except Exception as e:
        logger.error(f"Error retrieving conversation memory: {e}")
        return "No se pudo acceder al historial de conversación."


@tool
def save_conversation_memory(user_id: str, conversation_summary: str) -> str:
    """
    Save conversation summary for a specific user (long-term use case placeholder).

    Args:
        user_id: The unique identifier for the user
        conversation_summary: Summary of the conversation to save

    Returns:
        str: Confirmation message about the save operation
    """
    logger.info(f"Saving conversation memory for user: {user_id}")

    try:
        if not user_id or not conversation_summary:
            return "Error: Información insuficiente para guardar la memoria."
        # Persist minimal long-term summary record
        ltm = LongTermMemoryService(FileLongTermMemoryRepository())
        ltm.save_summary({
            "id_user": user_id,
            "resumen": conversation_summary,
        })
        return "Memoria de conversación guardada exitosamente."

    except Exception as e:
        logger.error(f"Error saving conversation memory: {e}")
        return "Error al guardar la memoria de conversación."


@tool
def clear_conversation_memory(user_id: str, session_id: str | None = None) -> str:
    """
    Clear short-term conversation memory for a specific session.

    Args:
        user_id: The unique identifier for the user
        session_id: Conversation/session identifier

    Returns:
        str: Confirmation message about the clear operation
    """
    logger.info(f"Clearing conversation memory for user: {user_id}")

    try:
        if not session_id:
            return "Error: session_id requerido para limpiar memoria."
        get_memory_service().clear_session(session_id)
        logger.info(
            f"Conversation memory cleared for user {user_id} session {session_id}"
        )
        return "Memoria de conversación limpiada exitosamente."

    except Exception as e:
        logger.error(f"Error clearing conversation memory: {e}")
        return "Error al limpiar la memoria de conversación."
