"""
Domain model for conversation state management.

This module defines the conversation state structure that maintains
the context and flow of agent conversations following domain-driven design principles.
"""

from typing import TypedDict, Optional, List, Dict, Any


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