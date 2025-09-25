"""Entrevistador node for Agente_Perfilamiento."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.agents.tools.entity_tools import (
    get_entity_memory,
    upsert_entity_memory,
)
from agente_perfilamiento.agents.tools.memory_tools import get_conversation_memory
from agente_perfilamiento.domain.models.conversation_state import (
    ConversationState,
    apply_state_defaults,
)
from agente_perfilamiento.infrastructure.config.settings import settings
from agente_perfilamiento.infrastructure.persistence.provider import get_memory_service


class EntrevistadorAgent(BaseAgent):
    """Agent dedicated to asking questions and collecting responses."""

    def __init__(self, max_questions: int = 15) -> None:
        super().__init__("entrevistador_agent")
        self.max_questions = max_questions

    def get_tools(self) -> List[BaseTool]:
        # Puede leer memoria de conversación y actualizar/leer entidad
        return [get_conversation_memory, get_entity_memory, upsert_entity_memory]

    def get_fallback_response(self) -> str:
        return "Voy a continuar con una pregunta breve para conocerte mejor."

    def process(self, state: ConversationState) -> ConversationState:
        self.logger.info("Processing entrevistador node")

        state = apply_state_defaults(state)

        conversation_history: List[Dict[str, str]] = list(
            state.get("conversation_history") or []
        )

        raw_profile: Dict[str, Any] = state.get("user_profile") or {}
        user_profile: Dict[str, Any] = {
            "respuestas_test": list(raw_profile.get("respuestas_test") or []),
            "intereses": list(raw_profile.get("intereses") or []),
            "valores": list(raw_profile.get("valores") or []),
        }
        for key, value in raw_profile.items():
            if key not in user_profile:
                user_profile[key] = value

        current_question_index = int(state.get("current_question_index") or 0)

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

        user_input = (state.get("input_usuario") or "").strip()
        if user_input:
            conversation_history.append({"role": "user", "content": user_input})
            user_profile.setdefault("respuestas_test", [])
            user_profile["respuestas_test"].append(user_input)
            current_question_index += 1

        farewell_keywords = ["terminar", "fin", "listo", "basta", "suficiente"]
        stop_requested = (
            any(keyword in user_input.lower() for keyword in farewell_keywords)
            if user_input
            else False
        )
        ready_for_analysis = stop_requested or (
            current_question_index >= self.max_questions
        )

        summary_payload: Optional[Dict[str, Any]] = state.get("interview_summary")
        summary_path: Optional[str] = state.get("interview_summary_path")

        final_trigger = "<<FIN_ENTREVISTA>>"

        if not ready_for_analysis:
            ai_response = self.execute_agent(state)
            if final_trigger in ai_response:
                ready_for_analysis = True
                ai_response = ai_response.replace(final_trigger, "").strip()
            response = ai_response or "Gracias. Voy a pasar tu perfil al analisis."
        else:
            response = "Gracias. Voy a pasar tu perfil al analisis."

        if ready_for_analysis and summary_payload is None:
            summary_payload = self._build_summary_payload(
                state=state,
                conversation_history=conversation_history,
                user_profile=user_profile,
                question_index=current_question_index,
            )
            summary_path = self._persist_summary(summary_payload)
            response = "Gracias. Voy a pasar tu perfil al analisis."

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
            "conversation_history": conversation_history,
            "user_profile": user_profile,
            "current_question_index": current_question_index,
            "ready_for_analysis": ready_for_analysis,
            "interview_summary": summary_payload,
            "interview_summary_path": summary_path,
            "next_node": None,
        }

    @staticmethod
    def _build_summary_payload(
        state: ConversationState,
        conversation_history: List[Dict[str, str]],
        user_profile: Dict[str, Any],
        question_index: int,
    ) -> Dict[str, Any]:
        return {
            "id_user": state.get("id_user"),
            "session_id": state.get("id_conversacion"),
            "created_at": datetime.utcnow().isoformat(),
            "current_question_index": question_index,
            "conversation_history": conversation_history,
            "user_profile": user_profile,
        }

    def _persist_summary(self, payload: Dict[str, Any]) -> str:
        base_dir = Path(settings.data_dir) / "interviews"
        base_dir.mkdir(parents=True, exist_ok=True)

        user_id = payload.get("id_user") or "unknown"
        session_id = payload.get("session_id") or "session"
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"{user_id}_{session_id}_{timestamp}.json"
        path = base_dir / filename

        with path.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)

        self.logger.info("Saved interview summary at %s", path)
        return str(path)


entrevistador_agent = EntrevistadorAgent()


def entrevistador_node(state: ConversationState) -> ConversationState:
    return entrevistador_agent.process(state)
