"""
Entity memory tools for agents to read/update user profile-like attributes.
"""

import json
from typing import Dict

from langchain_core.tools import tool

from agente_perfilamiento.domain.services.entity_memory_service import (
    EntityMemoryService,
)
from agente_perfilamiento.adapters.file_entity_repository import (
    FileEntityMemoryRepository,
)
from agente_perfilamiento.infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


def _service() -> EntityMemoryService:
    return EntityMemoryService(FileEntityMemoryRepository())


@tool
def get_entity_memory(user_id: str) -> str:
    """Get stored entity memory (profile attributes) for a user as JSON string."""
    try:
        data = _service().get(user_id)
        return json.dumps(data, ensure_ascii=False)
    except Exception as e:
        logger.error(f"get_entity_memory error: {e}")
        return "{}"


@tool
def upsert_entity_memory(user_id: str, attributes_json: str) -> str:
    """Merge and store entity attributes for a user. Pass attributes as JSON string."""
    try:
        attrs: Dict = json.loads(attributes_json) if attributes_json else {}
        _service().upsert(user_id, attrs)
        return "OK"
    except Exception as e:
        logger.error(f"upsert_entity_memory error: {e}")
        return "ERROR"


@tool
def clear_entity_memory(user_id: str) -> str:
    """Clear all entity memory for a user."""
    try:
        _service().clear(user_id)
        return "OK"
    except Exception as e:
        logger.error(f"clear_entity_memory error: {e}")
        return "ERROR"
