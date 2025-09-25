"""
Main entry point for Agente_Perfilamiento.

This module provides the main execution logic for the chat agent,
following hexagonal architecture principles with clean separation of concerns.
"""

import uuid
from datetime import datetime
from typing import Optional

from agente_perfilamiento.application.orchestrator import app
from agente_perfilamiento.domain.services.memory_service import MemoryService
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.config.settings import (
    ensure_data_directories,
    settings,
)
from agente_perfilamiento.infrastructure.logging.logger import (
    configure_logging,
    get_logger,
)
from agente_perfilamiento.adapters.in_memory_repository import (
    InMemoryMemoryRepository,
)
from agente_perfilamiento.infrastructure.persistence.provider import (
    get_memory_service,
    set_memory_service,
)

logger = get_logger(__name__)


def create_initial_state(
    user_id: str, user_input: str, conversation_id: Optional[str] = None
) -> ConversationState:
    """
    Creates initial conversation state for a new session.

    Args:
        user_id: Unique identifier for the user
        user_input: Initial user message
        conversation_id: Optional existing conversation ID

    Returns:
        Initial conversation state
    """
    if not conversation_id:
        conversation_id = str(uuid.uuid4())

    return ConversationState(
        id_user=user_id,
        id_conversacion=conversation_id,
        input_usuario=user_input,
        intencion=None,
        mensajes_previos=[],
        fecha_inicio=datetime.now().isoformat(),
        next_node=None,
        current_step="initial",
        conversation_complete=False,
        context_data={},
    )


def process_conversation(
    user_id: str,
    user_input: str,
    conversation_id: Optional[str] = None,
    existing_state: Optional[ConversationState] = None,
) -> ConversationState:
    """
    Processes a conversation turn through the agent orchestrator.

    Args:
        user_id: Unique identifier for the user
        user_input: User's message input
        conversation_id: Optional existing conversation ID

    Returns:
        Updated conversation state after processing
    """
    logger.info(f"Processing conversation for user {user_id}")

    # Create or update conversation state
    if existing_state:
        state = {**existing_state}
        # Ensure we track the conversation id consistently
        if conversation_id:
            state["id_conversacion"] = conversation_id
        conversation_id = state.get("id_conversacion")
        messages = list(state.get("mensajes_previos", []) or [])
    else:
        state = create_initial_state(user_id, user_input, conversation_id)
        conversation_id = state["id_conversacion"]
        messages = []

    # Update input and message history
    state["input_usuario"] = user_input
    messages.append({"role": "user", "content": user_input})
    state["mensajes_previos"] = messages

    # Append user message to short-term memory (router as default agent context)
    try:
        mem = get_memory_service()
        mem.append_and_get_window(
            agent_name="router_agent",
            session_id=state["id_conversacion"],
            role="user",
            content=user_input,
        )
    except Exception:
        pass

    try:
        # Process through agent orchestrator
        result = app.invoke(state)
        logger.info("Conversation processed successfully")
        return result

    except Exception as e:
        logger.error(f"Error processing conversation: {e}")
        # Return state with error message
        state["mensajes_previos"].append(
            {
                "role": "assistant",
                "content": f"Lo siento, ocurrió un error procesando tu solicitud. Por favor intenta de nuevo.",
            }
        )
        return state


def main():
    """
    Main entry point for command-line execution.

    This provides a simple CLI interface for testing the agent.
    For web interfaces, use the appropriate framework integration.
    """
    configure_logging(settings.log_level)
    ensure_data_directories()

    # Initialize short-term memory service (in-memory adapter for now)
    repo = InMemoryMemoryRepository()
    memory_service = MemoryService(
        repository=repo,
        ttl_seconds=settings.memory_ttl_seconds,
        max_items_per_agent=settings.memory_max_items_per_agent,
        window_limit=settings.memory_window_limit,
    )
    set_memory_service(memory_service)

    logger.info("Starting Agente_Perfilamiento CLI")

    print(f"Bienvenido a itti Academy")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("-" * 50)

    user_id = input("¿Mba'eteko pio? Bienvenido a itti Academy! ¿Cuál es tu nombre? : ").strip()
    if not user_id:
        user_id = "cli_user"

    conversation_id = str(uuid.uuid4())
    current_state: Optional[ConversationState] = None
    last_rendered_index = 0

    while True:
        try:
            user_input = input(f"\n[{user_id}]: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # Process conversation
            result = process_conversation(
                user_id=user_id,
                user_input=user_input,
                conversation_id=conversation_id,
                existing_state=current_state,
            )

            # Display only new assistant responses
            messages = result.get("mensajes_previos", []) or []
            new_messages = messages[last_rendered_index:]
            for message in new_messages:
                if message.get("role") == "assistant":
                    print(f"[Assistant]: {message['content']}")
            last_rendered_index = len(messages)

            # Update conversation ID for continuation
            conversation_id = result["id_conversacion"]
            current_state = result

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
