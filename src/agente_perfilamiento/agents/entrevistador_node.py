"""Entrevistador node for Agente_Perfilamiento."""

import json
from datetime import datetime
from pathlib import Path
import re
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

        messages = state.get("mensajes_previos", []) or []
        structured_profile: Optional[Dict[str, Any]] = None

        if ready_for_analysis and summary_payload is None:
            structured_profile = self._generate_structured_profile(
                base_state=state,
                conversation_history=conversation_history,
                user_profile=user_profile,
                assistant_messages=messages,
            )
            summary_payload = self._build_summary_payload(
                state=state,
                conversation_history=conversation_history,
                user_profile=user_profile,
                question_index=current_question_index,
                structured_profile=structured_profile,
            )
            summary_path = self._persist_summary(summary_payload)
            response = "Gracias. Voy a pasar tu perfil al analisis."

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

    def _generate_structured_profile(
        self,
        base_state: ConversationState,
        conversation_history: List[Dict[str, str]],
        user_profile: Dict[str, Any],
        assistant_messages: List[Dict[str, str]],
    ) -> Optional[Dict[str, Any]]:
        """Ask the interviewer LLM for the structured JSON profile."""

        if not conversation_history:
            return None

        transcript = self._build_transcript(assistant_messages, conversation_history)
        if not transcript:
            return None

        summary_input = {
            "perfil_nombre": base_state.get("id_user") or "",
            "id_conversacion": base_state.get("id_conversacion"),
            "transcript": transcript,
            "user_profile": user_profile,
        }

        summary_instruction = (
            "Ignora cualquier instrucción previa que te obligue a finalizar con <<FIN_ENTREVISTA>>. "
            "Genera únicamente un JSON válido siguiendo exactamente la estructura solicitada. "
            "No incluyas texto adicional, explicaciones ni formato markdown."
        )
        schema_hint = json.dumps(
            {
                "perfil_nombre": "<texto>",
                "dimensiones_mapeadas": {
                    "intereses": ["<tag>", "<tag>"],
                    "estilo_aprendizaje": ["<tag>", "<tag>"],
                    "competencias_tecnicas_iniciales": {"<competencia>": "<nivel>"},
                    "valores_aspiraciones": ["<tag>"],
                },
                "tags_acumulados_vector": {"<tag>": 1},
                "Resumen": {},
            },
            ensure_ascii=False,
            indent=2,
        )

        summary_state = {
            **base_state,
            "input_usuario": (
                f"{summary_instruction}\n"
                f"Formato esperado:\n{schema_hint}\n\n"
                f"Datos de referencia:\n"
                + json.dumps(summary_input, ensure_ascii=False)
            ),
        }

        response = self.execute_agent(summary_state)
        structured = self._extract_json_block(response)
        if not structured:
            self.logger.warning("Entrevistador agent did not return parsable structured profile")
        return structured

    @staticmethod
    def _build_transcript(
        assistant_messages: List[Dict[str, str]],
        conversation_history: List[Dict[str, str]],
    ) -> List[Dict[str, str]]:
        transcript: List[Dict[str, str]] = []
        assistant_contents = [
            msg.get("content", "")
            for msg in assistant_messages
            if isinstance(msg, dict) and msg.get("role") == "assistant"
        ]

        for idx, entry in enumerate(conversation_history):
            user_content = entry.get("content") if isinstance(entry, dict) else None
            if idx < len(assistant_contents):
                question = assistant_contents[idx]
                if question:
                    transcript.append({"role": "assistant", "content": question})
            if user_content:
                transcript.append({"role": "user", "content": user_content})

        return transcript

    @staticmethod
    def _extract_json_block(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if match:
                candidate = match.group(0)
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    return None
        return None

    def _build_summary_payload(
        self,
        state: ConversationState,
        conversation_history: List[Dict[str, str]],
        user_profile: Dict[str, Any],
        question_index: int,
        structured_profile: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "id_user": state.get("id_user"),
            "session_id": state.get("id_conversacion"),
            "created_at": datetime.utcnow().isoformat(),
            "current_question_index": question_index,
            "conversation_history": conversation_history,
            "user_profile": user_profile,
        }
        if structured_profile:
            payload["structured_profile"] = structured_profile
        return payload

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
