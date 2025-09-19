"""
Router node for Agente_Perfilamiento agent.

This node analyzes user input and determines the appropriate
agent/node to handle the conversation flow.
"""

from typing import List

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.memory.provider import get_memory_service


class RouterAgent(BaseAgent):
    """Agent class for handling conversation routing logic."""

    def __init__(self):
        super().__init__("router_agent")

    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the router agent."""
        # Router typically doesn't need tools, it makes routing decisions
        return []

    def get_fallback_response(self) -> str:
        """Get fallback response for router agent."""
        return "fallback"  # Default routing destination

    def determine_route(self, state: ConversationState) -> str:
        """
        Determine the next node based on conversation state.

        Args:
            state: Current conversation state

        Returns:
            str: Name of the next node to route to
        """
        user_input = state.get("input_usuario", "").lower().strip()
        messages = state.get("mensajes_previos", [])
        saludo_mostrado = state.get("saludo_mostrado", False)

        # TODO refactor this logic to use AI agent for more complex routing decisions
        # # Simple routing logic
        # if not saludo_mostrado:
        #     return "welcome"
        # Check for farewell intentions
        farewell_keywords = [
            "adios",
            "adiós",
            "hasta luego",
            "chao",
            "terminar",
            "salir",
            "fin",
        ]
        if any(keyword in user_input for keyword in farewell_keywords):
            return "final"

        # For now, default to fallback for other cases
        # In a real implementation, this would include more sophisticated routing logic
        return "perfilamiento"

    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the router agent.

        Args:
            state: Current conversation state

        Returns:
            ConversationState: Updated conversation state with routing decision
        """
        self.logger.info("Processing router node")

        try:
            # Determine the next route using routing logic
            next_route = self.determine_route(state)

            # Optionally use AI agent for more complex routing decisions
            # ai_route = self.execute_agent(state)
            # if ai_route.strip() in ["welcome", "final", "fallback"]:
            #     next_route = ai_route.strip()

            self.logger.info(f"Routing to: {next_route}")

        except Exception as e:
            self.logger.error(f"Error in router processing: {e}")
            next_route = "fallback"

        # Append latest user input to the target agent's short-term memory window
        try:
            session_id = state.get("id_conversacion", "")
            user_input = state.get("input_usuario", "")
            if session_id and user_input:
                target_agent_map = {
                    "welcome": "welcome_agent",
                    "perfilamiento": "perfilamiento_agent",
                    "final": "final_agent",
                    "fallback": "fallback_agent",
                }
                target_agent = target_agent_map.get(next_route)
                if target_agent:
                    get_memory_service().append_and_get_window(
                        agent_name=target_agent,
                        session_id=session_id,
                        role="user",
                        content=user_input,
                    )
        except Exception:
            pass

        self.logger.debug("Router node processing completed")

        return {**state, "next_node": next_route}


# Create instance and function wrapper for LangGraph compatibility
router_agent = RouterAgent()


def router_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for router agent to maintain LangGraph compatibility.

    Args:
        state: Current conversation state

    Returns:
        Updated conversation state with routing decision
    """
    return router_agent.process(state)
