"""
perfilamiento node for Agente_Perfilamiento agent.

This node handles initial user interactions and provides guidance to users
with context awareness using conversation memory.
"""

from typing import List

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.memory_tools import get_conversation_memory
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.memory.provider import get_memory_service


class PerfilamientoAgent(BaseAgent):
    """Agent class for handling guidance interactions."""

    def __init__(self):
        super().__init__("perfilamiento_agent")

    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the perfilamiento agent."""
        return [get_conversation_memory]

    def get_fallback_response(self) -> str:
        """Get fallback response for perfilamiento agent."""
        return "¡Bienvenido a Agente_Perfilamiento! ¿En qué puedo ayudarte hoy?"

    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the perfilamiento agent.

        Args:
            state: Current conversation state

        Returns:
            ConversationState: Updated conversation state with perfilamiento response
        """
        self.logger.info("Processing perfilamiento node")

        # Check if perfilamiento has already been shown
        if state.get("hoja_ruta"):
            self.logger.debug("Hoja de ruta terminada, devolviendo el estado actual")
            return state

        # Fetch short-term memory window for this agent/session and attach to context
        try:
            memory = get_memory_service()
            session_id = state.get("id_conversacion", "")
            window = memory.get_window(self.agent_name, session_id)
            context_data = state.get("context_data", {}) or {}
            context_data["short_term_memory"] = window
            state = {**state, "context_data": context_data}
        except Exception:
            # If memory service not available, continue without window
            pass

        # Execute the agent to get response
        response = self.execute_agent(state)

        # Update conversation history
        messages = state.get("mensajes_previos", [])
        messages.append({"role": "assistant", "content": response})

        # Persist assistant response in short-term memory
        try:
            if state.get("id_conversacion"):
                get_memory_service().append_and_get_window(
                    agent_name=self.agent_name,
                    session_id=state["id_conversacion"],
                    role="assistant",
                    content=response,
                )
        except Exception:
            pass

        self.logger.debug("Perfilamiento node processing completed")

        return {
            **state,
            "mensajes_previos": messages,
            "hoja_ruta": True,
            "next_node": None,  # Let router determine next step
        }


# Create instance and function wrapper for LangGraph compatibility
perfilamiento_agent = PerfilamientoAgent()


def perfilamiento_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for perfilamiento agent to maintain LangGraph compatibility.

    Args:
        state: Current conversation state

    Returns:
        Updated conversation state with perfilamiento response
    """
    return perfilamiento_agent.process(state)
