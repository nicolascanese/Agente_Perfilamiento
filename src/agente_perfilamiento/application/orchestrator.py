"""
LangGraph orchestrator for the Agente_Perfilamiento agent.

This module contains the main graph construction logic that orchestrates
conversation flow between different agent nodes following hexagonal architecture principles.
"""

from langchain_core.runnables import RunnableLambda
from langgraph.graph import END, StateGraph

from agente_perfilamiento.agents.fallback_node import fallback_node
from agente_perfilamiento.agents.final_node import final_node
from agente_perfilamiento.agents.memory_node import memory_node
from agente_perfilamiento.agents.router_node import router_node
from agente_perfilamiento.agents.welcome_node import welcome_node
from agente_perfilamiento.agents.entrevistador_node import entrevistador_node
from agente_perfilamiento.agents.analista_node import analista_node
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.logging.logger import get_logger

logger = get_logger(__name__)


def create_agent_graph() -> StateGraph:
    """
    Creates and configures the LangGraph state graph for conversation orchestration.

    Returns:
        StateGraph: The configured conversation graph ready for compilation
    """
    logger.info("Creating agent graph for Agente_Perfilamiento")

    # Initialize the graph with conversation state
    builder = StateGraph(ConversationState)

    # Set entry point to router
    builder.set_entry_point("router")

    # Add core nodes
    builder.add_node("router", RunnableLambda(router_node))
    builder.add_node("welcome", RunnableLambda(welcome_node))
    builder.add_node("final", RunnableLambda(final_node))
    builder.add_node("memory", RunnableLambda(memory_node))
    builder.add_node("entrevistador", RunnableLambda(entrevistador_node))
    builder.add_node("analista", RunnableLambda(analista_node))
    builder.add_node("fallback", RunnableLambda(fallback_node))

    # Add edges for conversation flow
    builder.add_edge("welcome", END)
    builder.add_edge("fallback", END)
    builder.add_edge("entrevistador", END)
    builder.add_edge("analista", END)
    builder.add_edge("final", "memory")
    builder.add_edge("memory", END)

    # Add conditional routing from router
    builder.add_conditional_edges(
        "router",
        lambda state: state["next_node"],
        {
            "welcome": "welcome",
            "entrevistador": "entrevistador",
            "analista": "analista",
            "final": "final",
            "fallback": "fallback",
            # Additional nodes can be added here based on specific agent requirements
        },
    )

    logger.info("Agent graph created successfully")
    return builder


def get_compiled_agent():
    """
    Creates and compiles the agent graph for execution.

    Returns:
        Compiled LangGraph agent ready for invocation
    """
    builder = create_agent_graph()
    app = builder.compile()

    logger.info("Agent graph compiled and ready for execution")
    return app


# Create the compiled agent instance
app = get_compiled_agent()
