import os
from pathlib import Path

import pytest

from agente_perfilamiento.agents.base_agent import BaseAgent
from agente_perfilamiento.domain.services.memory_service import MemoryService
from agente_perfilamiento.adapters.in_memory_repository import (
    InMemoryMemoryRepository,
)
from agente_perfilamiento.infrastructure.persistence.provider import (
    get_memory_service,
    set_memory_service,
)
from agente_perfilamiento.infrastructure.logging.logger import configure_logging
from agente_perfilamiento.infrastructure.config.settings import settings
from agente_perfilamiento.main import process_conversation


@pytest.mark.usefixtures("caplog")
def test_interview_analyst_flow(monkeypatch, caplog):
    os.environ.setdefault("LLM_API_KEY", "test-key")
    os.environ.setdefault("LLM_MODEL", "gpt-4o-mini")
    os.environ.setdefault("LLM_PROVIDER", "openai")

    configure_logging("WARNING")

    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repo,
        ttl_seconds=settings.memory_ttl_seconds,
        max_items_per_agent=settings.memory_max_items_per_agent,
        window_limit=settings.memory_window_limit,
    )
    set_memory_service(memory_service)

    questions = {
        1: "Pregunta 1",
        2: "Pregunta 2",
        3: "Pregunta 3",
        4: "Pregunta 4",
        5: "Pregunta 5",
    }

    def fake_execute_agent(self, state, **kwargs):
        name = getattr(self, "agent_name", "")
        if name == "welcome_agent":
            return "Bienvenido, empecemos la entrevista."
        if name == "entrevistador_agent":
            idx = int(state.get("current_question_index") or 0)
            return questions.get(idx, "Pregunta adicional")
        if name == "analista_agent":
            return (
                "Resumen generado. Codigo Holland: ASE. Recomendaciones en Paraguay: "
                "Diseno UX, Ingenieria de Software, Gestion de Proyectos."
            )
        if name == "final_agent":
            return "Gracias por compartir. Aqui tienes los proximos pasos."
        if name == "memory_agent":
            return "Memoria consolidada y guardada."
        return "Mensaje auxiliar."

    monkeypatch.setattr(BaseAgent, "execute_agent", fake_execute_agent, raising=False)

    conversation_id = "test-flow"
    user_id = "user-test"
    turns = [
        "hola",
        "Me gusta programar y aprender cosas nuevas.",
        "Disfruto cuando trabajamos en grupo para lograr algo grande.",
        "Definitivamente crear algo nuevo me entusiasma.",
        "terminar",
        "ok",
        "gracias",
    ]

    caplog.set_level("INFO")
    state = None
    current_conversation_id = conversation_id

    for turn in turns:
        state = process_conversation(
            user_id=user_id,
            user_input=turn,
            conversation_id=current_conversation_id,
            existing_state=state,
        )
        current_conversation_id = state["id_conversacion"]

    assert state.get("evaluation_complete") is True
    assert state.get("agent_recommendations")
    assert state.get("interview_summary")

    summary_path = state.get("interview_summary_path")
    assert summary_path
    summary_file = Path(summary_path)
    assert summary_file.exists()

    interviewer_responses = [
        msg["content"]
        for msg in state.get("mensajes_previos", [])
        if msg.get("role") == "assistant" and msg["content"].startswith("Pregunta")
    ]
    assert len(interviewer_responses) >= 1

    memory = get_memory_service()
    interview_window = memory.get_window("entrevistador_agent", conversation_id)
    session_window = memory.get_window("session_agent", conversation_id)

    assert len(interview_window) >= 1
    assert len(session_window) >= len(interview_window)

    final_messages = [
        msg["content"]
        for msg in state.get("mensajes_previos", [])
        if msg.get("role") == "assistant" and "proximos pasos" in msg.get("content", "")
    ]
    assert final_messages

    analyst_messages = [
        msg["content"]
        for msg in state.get("mensajes_previos", [])
        if msg.get("role") == "assistant" and "Resumen generado" in msg.get("content", "")
    ]
    assert analyst_messages

    # Cleanup generated summary file to keep test artifacts tidy
    if summary_file.exists():
        summary_file.unlink()
