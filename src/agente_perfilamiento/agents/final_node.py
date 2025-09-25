"""
Final node for Agente_Perfilamiento agent.

This node handles conversation finalization and provides appropriate
closing responses with summary capabilities.
"""

from typing import List

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.memory_tools import save_conversation_memory
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.persistence.provider import get_memory_service


class FinalAgent(BaseAgent):
    """Agent class for handling conversation finalization."""

    def __init__(self):
        super().__init__("final_agent")

    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the final agent."""
        return [save_conversation_memory]

    def get_fallback_response(self) -> str:
        """Get fallback response for final agent."""
        return "¡Gracias por usar Agente_Perfilamiento! ¡Que tengas un excelente día!"

    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the final agent.

        Args:
            state: Current conversation state

        Returns:
            ConversationState: Updated conversation state with final response
        """
        self.logger.info("Processing final node")

        # Fetch short-term memory window for this agent/session and attach to context
        try:
            memory = get_memory_service()
            session_id = state.get("id_conversacion", "")
            window = memory.get_window(self.agent_name, session_id)
            context_data = state.get("context_data", {}) or {}
            context_data["short_term_memory"] = window
            state = {**state, "context_data": context_data}
        except Exception:
            pass

        # Execute the agent to get closing response
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
                # Session-wide stream for full summaries
                get_memory_service().append_and_get_window(
                    agent_name="session_agent",
                    session_id=state["id_conversacion"],
                    role="assistant",
                    content=response,
                )
        except Exception:
            pass

        self.logger.debug("Final node processing completed")

        return {
            **state,
            "mensajes_previos": messages,
            "conversation_finished": True,
            "next_node": "memory",  # Proceed to memory node to save conversation
        }


# Create instance and function wrapper for LangGraph compatibility
final_agent = FinalAgent()


def final_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for final agent to maintain LangGraph compatibility.

    Args:
        state: Current conversation state

    Returns:
        Updated conversation state with final response
    """
    return final_agent.process(state)
