"""
Analista node for Agente_Perfilamiento agent.

This node analyzes collected data and produces recommendations.
"""

import json
from typing import List

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.memory_tools import get_conversation_memory
from agente_perfilamiento.domain.models.conversation_state import (
    ConversationState,
    apply_state_defaults,
)
from agente_perfilamiento.infrastructure.persistence.provider import get_memory_service


class AnalistaAgent(BaseAgent):
    """Agent for analysis and recommendations only."""

    def __init__(self):
        super().__init__("analista_agent")

    def get_tools(self) -> List[BaseTool]:
        # Solo lectura de memoria de conversación para contexto
        return [get_conversation_memory]

    def get_fallback_response(self) -> str:
        return "Análisis no disponible ahora. Retomaré con recomendaciones resumidas." 

    def process(self, state: ConversationState) -> ConversationState:
        self.logger.info("Processing analista node")

        state = apply_state_defaults(state)

        # Attach short-term memory window to context
        try:
            memory = get_memory_service()
            session_id = state.get("id_conversacion", "")
            window = memory.get_window(self.agent_name, session_id)
            context_data = state.get("context_data", {}) or {}
            context_data["short_term_memory"] = window
            state = {**state, "context_data": context_data}
        except Exception:
            pass

        # Compose a synthetic user_message that includes full profile/context for analysis
        summary_input = state.get("interview_summary")
        if not summary_input:
            conversation_history = state.get("conversation_history") or []
            user_profile = state.get("user_profile") or {}
            summary_input = {
                "conversation_history": conversation_history,
                "user_profile": user_profile,
                "current_question_index": state.get("current_question_index", 0),
            }
        if state.get("interview_summary_path"):
            summary_input = {**summary_input, "summary_path": state["interview_summary_path"]}
        analysis_user_message = (
            "Analiza el siguiente perfil y entrega el resultado en el formato solicitado.\n\n"
            + json.dumps(summary_input, ensure_ascii=False)
        )

        # Execute agent with the synthetic message
        exec_state = {**state, "input_usuario": analysis_user_message}
        response = self.execute_agent(exec_state)

        # Update messages and memory
        messages = state.get("mensajes_previos", []) or []
        messages.append({"role": "assistant", "content": response})

        try:
            if state.get("id_conversacion"):
                get_memory_service().append_and_get_window(
                    agent_name=self.agent_name,
                    session_id=state["id_conversacion"],
                    role="assistant",
                    content=response,
                )
                get_memory_service().append_and_get_window(
                    agent_name="session_agent",
                    session_id=state["id_conversacion"],
                    role="assistant",
                    content=response,
                )
        except Exception:
            pass

        return {
            **state,
            "mensajes_previos": messages,
            "evaluation_complete": True,
            "agent_recommendations": response,
            "ready_for_analysis": False,
            "next_node": None,  # router decides next
        }


analista_agent = AnalistaAgent()


def analista_node(state: ConversationState) -> ConversationState:
    return analista_agent.process(state)
