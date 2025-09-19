"""
Application service for managing short-term memory windows.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from agente_perfilamiento.application.ports.memory_repository import MemoryRepository
from agente_perfilamiento.domain.memory.models import ShortTermMemoryItem
from agente_perfilamiento.infrastructure.logging.logger import get_logger


logger = get_logger(__name__)


class MemoryService:
    def __init__(
        self,
        repository: MemoryRepository,
        ttl_seconds: Optional[int] = None,
        max_items_per_agent: Optional[int] = None,
        window_limit: Optional[int] = None,
    ) -> None:
        self._repo = repository
        self._ttl_seconds = ttl_seconds
        self._max_items = max_items_per_agent
        self._window_limit = window_limit

    def append_and_get_window(
        self,
        agent_name: str,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        item = ShortTermMemoryItem(
            agent_name=agent_name,
            session_id=session_id,
            role=role,
            content=content,
            metadata=metadata,
        )
        self._repo.save(item)
        self._repo.prune(agent_name, session_id, self._ttl_seconds, self._max_items)

        window_limit = limit if limit is not None else self._window_limit
        items = self._repo.get_recent(agent_name, session_id, window_limit)
        result = [self._to_public_dict(i) for i in items]
        logger.debug(
            f"memory.append_and_get_window agent={agent_name} session={session_id} size={len(result)}"
        )
        return result

    def get_window(
        self, agent_name: str, session_id: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        window_limit = limit if limit is not None else self._window_limit
        items = self._repo.get_recent(agent_name, session_id, window_limit)
        result = [self._to_public_dict(i) for i in items]
        logger.debug(
            f"memory.get_window agent={agent_name} session={session_id} size={len(result)}"
        )
        return result

    def clear_session(self, session_id: str) -> None:
        self._repo.clear_session(session_id)
        logger.info(f"memory.clear_session session={session_id}")

    @staticmethod
    def _to_public_dict(item: ShortTermMemoryItem) -> Dict[str, Any]:
        return {
            "role": item.role,
            "content": item.content,
            "created_at": item.created_at.isoformat(),
            "agent_name": item.agent_name,
        }

