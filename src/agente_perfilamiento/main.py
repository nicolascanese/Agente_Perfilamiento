"""
Main entry point for Agente_Perfilamiento.

This module provides the main execution logic for the chat agent,
following hexagonal architecture principles with clean separation of concerns.
"""

import uuid
from datetime import datetime
from typing import Optional

# from agente_perfilamiento.adapters.conversation_repository import (
#     FileConversationRepository,
# )
from agente_perfilamiento.application.orchestrator import app
from agente_perfilamiento.domain.models.conversation_state import ConversationState
from agente_perfilamiento.infrastructure.config.settings import (
    ensure_data_directories,
    settings,
)
from agente_perfilamiento.infrastructure.logging.logger import (
    configure_logging,
    get_logger,
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
    user_id: str, user_input: str, conversation_id: Optional[str] = None
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

    # Create or load conversation state
    state = create_initial_state(user_id, user_input, conversation_id)

    # Add user message to history
    state["mensajes_previos"].append({"role": "user", "content": user_input})

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


def save_conversation(state: ConversationState) -> None:
    """
    Saves conversation state to persistent storage.

    Args:
        state: Conversation state to save
    """
    try:
        repository = FileConversationRepository()
        repository.save_conversation(state)
        logger.info(f"Conversation {state['id_conversacion']} saved successfully")

    except Exception as e:
        logger.error(f"Error saving conversation: {e}")


def main():
    """
    Main entry point for command-line execution.

    This provides a simple CLI interface for testing the agent.
    For web interfaces, use the appropriate framework integration.
    """
    configure_logging(settings.log_level)
    ensure_data_directories()

    logger.info("Starting Agente_Perfilamiento CLI")

    print(f"Welcome to Agente_Perfilamiento!")
    print("Type 'quit' or 'exit' to end the conversation.")
    print("-" * 50)

    user_id = input("Enter your user ID (or press Enter for default): ").strip()
    if not user_id:
        user_id = "cli_user"

    conversation_id = str(uuid.uuid4())

    while True:
        try:
            user_input = input(f"\n[{user_id}]: ").strip()

            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break

            if not user_input:
                continue

            # Process conversation
            result = process_conversation(user_id, user_input, conversation_id)

            # Display assistant responses
            for message in result.get("mensajes_previos", []):
                if message["role"] == "assistant":
                    print(f"[Assistant]: {message['content']}")

            # Update conversation ID for continuation
            conversation_id = result["id_conversacion"]

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
