"""
Domain model for conversation state management.

This module defines the conversation state structure that maintains
the context and flow of agent conversations following domain-driven design principles.
"""

from typing import Any, Dict, List, Optional, TypedDict, cast


class ConversationState(TypedDict):
    """
    Represents the complete state of a conversation session.

    This TypedDict maintains all necessary information for conversation flow,
    including user context, message history, and workflow state management.
    """

    # User identification
    id_user: str
    id_conversacion: str

    # Current input and intent
    input_usuario: str
    intencion: Optional[str]

    # Conversation history
    mensajes_previos: Optional[List[Dict[str, str]]]
    fecha_inicio: Optional[str]

    # Navigation and flow control
    next_node: Optional[str]

    # Workflow state management
    current_step: str
    conversation_complete: bool

    # Additional context fields (can be extended based on specific domain needs)
    context_data: Optional[Dict[str, Any]]

    # Interview + analysis workflow state (specialized agents)
    conversation_history: Optional[List[Dict[str, Any]]]
    user_profile: Optional[Dict[str, Any]]  # { "respuestas_test": [], "intereses": [], "valores": [] }
    current_question_index: Optional[int]
    evaluation_complete: Optional[bool]
    agent_recommendations: Optional[Any]
    ready_for_analysis: Optional[bool]
    interview_summary: Optional[Dict[str, Any]]
    interview_summary_path: Optional[str]


# Default schema values (documentation/helper)
DEFAULT_STATE_SCHEMA: Dict[str, Any] = {
    "conversation_history": [],
    "user_profile": {
        "respuestas_test": [],
        "intereses": [],
        "valores": [],
    },
    "current_question_index": 0,
    "evaluation_complete": False,
    "agent_recommendations": None,
    "ready_for_analysis": False,
    "interview_summary": None,
    "interview_summary_path": None,
}


def apply_state_defaults(state: ConversationState) -> ConversationState:
    """Ensure extended workflow fields exist with sensible defaults."""

    merged: Dict[str, Any] = dict(state)

    if not merged.get("conversation_history"):
        merged["conversation_history"] = []

    user_profile = merged.get("user_profile") or {}
    if not isinstance(user_profile, dict):
        user_profile = {}
    merged_user_profile = {
        "respuestas_test": list(user_profile.get("respuestas_test") or []),
        "intereses": list(user_profile.get("intereses") or []),
        "valores": list(user_profile.get("valores") or []),
    }
    # Preserve any other custom attributes users might have stored
    for key, value in user_profile.items():
        if key not in merged_user_profile:
            merged_user_profile[key] = value
    merged["user_profile"] = merged_user_profile

    merged["current_question_index"] = int(merged.get("current_question_index") or 0)
    merged["evaluation_complete"] = bool(merged.get("evaluation_complete") or False)
    merged.setdefault("agent_recommendations", None)
    merged.setdefault("ready_for_analysis", False)
    merged.setdefault("interview_summary", None)
    merged.setdefault("interview_summary_path", None)

    return cast(ConversationState, merged)
