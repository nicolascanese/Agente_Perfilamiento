"""
Fallback node for Agente_Perfilamiento agent.

This node handles situations where other agents cannot adequately
process user requests or when errors occur in the conversation flow.
"""

from typing import List
from langchain_core.tools import BaseTool

from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.agents.base_agent import BaseAgent


class FallbackAgent(BaseAgent):
    """Agent class for handling fallback situations and errors."""
    
    def __init__(self):
        super().__init__("fallback_agent")
    
    def get_tools(self) -> List[BaseTool]:
        """Get the tools available for the fallback agent."""
        # Fallback agent typically doesn't need tools, focuses on graceful error handling
        return []
    
    def get_fallback_response(self) -> str:
        """Get fallback response for fallback agent."""
        return "Lo siento, no pude procesar tu solicitud. ¿Podrías reformularla de otra manera?"
    
    def process(self, state: ConversationState) -> ConversationState:
        """
        Process the conversation state through the fallback agent.
        
        Args:
            state: Current conversation state
            
        Returns:
            ConversationState: Updated conversation state with fallback response
        """
        self.logger.info("Processing fallback node")

        try:
            # Execute the agent to get a contextual fallback response
            response = self.execute_agent(state)
            self.logger.info("Fallback response generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error in fallback agent: {e}")
            response = self.get_fallback_response()

        # Update conversation history
        messages = state.get("mensajes_previos", [])
        messages.append({"role": "assistant", "content": response})

        self.logger.debug("Fallback node processing completed")

        return {
            **state,
            "mensajes_previos": messages,
            "fallback_triggered": True,
            "next_node": None  # End conversation or let router decide
        }


# Create instance and function wrapper for LangGraph compatibility
fallback_agent = FallbackAgent()


def fallback_node(state: ConversationState) -> ConversationState:
    """
    Function wrapper for fallback agent to maintain LangGraph compatibility.
    
    Args:
        state: Current conversation state
        
    Returns:
        Updated conversation state with fallback response
    """
    return fallback_agent.process(state)