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

        if messages and user_id:
            try:
                # Create a summary of the conversation
                conversation_text = ""
                for msg in messages[-10:]:  # Last 10 messages for context
                    role = msg.get("role", "unknown")
                    content = msg.get("content", "")
                    conversation_text += f"{role}: {content}\n"

                # Execute the agent to process and summarize the conversation
                summary = self.execute_agent(state, conversation_text=conversation_text)

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
