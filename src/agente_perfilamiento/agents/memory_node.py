"""
Memory node for Agente_Perfilamiento agent.

This node handles conversation memory processing, summarization,
and storage for future reference.
"""

from typing import List

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.memory_tools import (
    clear_conversation_memory,
    save_conversation_memory,
)
from agente_perfilamiento.domain.services.long_term_memory_service import (
    LongTermMemoryService,
)
from agente_perfilamiento.adapters.file_long_term_repository import (
    FileLongTermMemoryRepository,
)
from agente_perfilamiento.domain.models.conversation_state import ConversationState


class MemoryAgent(BaseAgent):
    """Agent class for handling conversation memory processing."""

    def __init__(self):
        super().__init__("memory_agent")

    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the memory agent."""
        return [save_conversation_memory, clear_conversation_memory]

    def get_fallback_response(self) -> str:
        """Get fallback response for memory agent."""
        return "Procesamiento de memoria completado."

    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the memory agent.

        Args:
            state: Current conversation state

        Returns:
            ConversationState: Updated conversation state after memory processing
        """
        self.logger.info("Processing memory node")

        # Get conversation messages for summarization
        messages = state.get("mensajes_previos", [])
        user_id = state.get("id_user", "")

        if user_id:
            try:
                # Create a summary source from the session-wide memory window (full conversation)
                conversation_text = ""
                try:
                    from agente_perfilamiento.infrastructure.memory.provider import (
                        get_memory_service,
                    )

                    session_id = state.get("id_conversacion", "")
                    full_window = (
                        get_memory_service().get_window(
                            agent_name="session_agent", session_id=session_id, limit=1000
                        )
                        if session_id
                        else []
                    )
                    source = full_window if full_window else (messages or [])
                except Exception:
                    source = messages or []

                for msg in source:
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    conversation_text += f"{role}: {content}\n"

                # Execute the agent to process and summarize the conversation
                summary = self.execute_agent(state, conversation_text=conversation_text)

                # Persist long-term summary with full state context (id_conversacion, fecha_inicio)
                try:
                    ltm = LongTermMemoryService(FileLongTermMemoryRepository())
                    ltm.save_summary(
                        {
                            "id_user": user_id,
                            "id_conversacion": state.get("id_conversacion", ""),
                            "fecha_inicio": state.get("fecha_inicio", ""),
                            "resumen": summary,
                        }
                    )
                except Exception:
                    pass

                self.logger.info("Memory processing completed successfully")

            except Exception as e:
                self.logger.error(f"Error in memory processing: {e}")
                summary = "Error procesando memoria de conversación."
        else:
            summary = "No hay conversación para procesar."

        self.logger.debug("Memory node processing completed")

        return {
            **state,
            "memory_processed": True,
            "memory_summary": summary,
            "next_node": None,  # End of conversation flow
        }


# Create instance and function wrapper for LangGraph compatibility
memory_agent = MemoryAgent()


def memory_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for memory agent to maintain LangGraph compatibility.

    Args:
        state: Current conversation state

    Returns:
        Updated conversation state after memory processing
    """
    return memory_agent.process(state)
