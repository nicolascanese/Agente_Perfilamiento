"""
Welcome node for Agente_Perfilamiento agent.

This node handles initial user interactions and provides welcome messages
with context awareness using conversation memory.
"""

from typing import List
from langchain_core.tools import BaseTool

from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.memory_tools import get_conversation_memory


class WelcomeAgent(BaseAgent):
    """Agent class for handling welcome interactions."""
    
    def __init__(self):
        super().__init__("welcome_agent")
    
    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the welcome agent."""
        return [get_conversation_memory]
    
    def get_fallback_response(self) -> str:
        """Get fallback response for welcome agent."""
        return "¡Bienvenido a Agente_Perfilamiento! ¿En qué puedo ayudarte hoy?"
    
    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the welcome agent.
        
        Args:
            state: Current conversation state
            
        Returns:
            ConversationState: Updated conversation state with welcome response
        """
        self.logger.info("Processing welcome node")
        
        # Check if welcome has already been shown
        if state.get("saludo_mostrado"):
            self.logger.debug("Welcome already shown, returning current state")
            return state

        # Execute the agent to get response
        response = self.execute_agent(state)

        # Update conversation history
        messages = state.get("mensajes_previos", [])
        messages.append({"role": "assistant", "content": response})

        self.logger.debug("Welcome node processing completed")

        return {
            **state,
            "mensajes_previos": messages,
            "saludo_mostrado": True,
            "next_node": None  # Let router determine next step
        }


# Create instance and function wrapper for LangGraph compatibility
welcome_agent = WelcomeAgent()


def welcome_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for welcome agent to maintain LangGraph compatibility.
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated conversation state with welcome response
    """
    return welcome_agent.process(state)