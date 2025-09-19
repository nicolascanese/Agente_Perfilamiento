"""
Application port for short-term memory repository.
"""

from abc import ABC, abstractmethod
from typing import List, Optional

from agente_perfilamiento.domain.memory.models import ShortTermMemoryItem


class MemoryRepository(ABC):
    @abstractmethod
    def save(self, item: ShortTermMemoryItem) -> None:  # pragma: no cover - interface
        ...

    @abstractmethod
    def get_recent(
        self, agent_name: str, session_id: str, limit: Optional[int] = None
    ) -> List[ShortTermMemoryItem]:  # pragma: no cover - interface
        ...

    @abstractmethod
    def prune(
        self,
        agent_name: str,
        session_id: str,
        ttl_seconds: Optional[int],
        max_items: Optional[int],
    ) -> None:  # pragma: no cover - interface
        ...

    @abstractmethod
    def clear_session(self, session_id: str) -> None:  # pragma: no cover - interface
        ...
