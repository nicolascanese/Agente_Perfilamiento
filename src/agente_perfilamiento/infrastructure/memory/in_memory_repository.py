"""
In-memory implementation of MemoryRepository.
"""

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Deque, Dict, List, Optional, Tuple

from agente_perfilamiento.application.ports.memory_repository import MemoryRepository
from agente_perfilamiento.domain.memory.models import ShortTermMemoryItem

Key = Tuple[str, str]  # (session_id, agent_name)


class InMemoryMemoryRepository(MemoryRepository):
    def __init__(self, default_maxlen: int = 500) -> None:
        self._store: Dict[Key, Deque[ShortTermMemoryItem]] = defaultdict(
            lambda: deque(maxlen=default_maxlen)
        )

    def save(self, item: ShortTermMemoryItem) -> None:
        key = (item.session_id, item.agent_name)
        self._store[key].append(item)

    def get_recent(
        self, agent_name: str, session_id: str, limit: Optional[int] = None
    ) -> List[ShortTermMemoryItem]:
        key = (session_id, agent_name)
        dq = self._store.get(key, deque())
        if limit is None or limit >= len(dq):
            return list(dq)
        # return the most recent items (deque is ordered oldest->newest)
        return list(dq)[-limit:]

    def prune(
        self,
        agent_name: str,
        session_id: str,
        ttl_seconds: Optional[int],
        max_items: Optional[int],
    ) -> None:
        key = (session_id, agent_name)
        dq = self._store.get(key)
        if not dq:
            return

        # prune by TTL
        if ttl_seconds is not None:
            cutoff = datetime.utcnow() - timedelta(seconds=ttl_seconds)
            # remove from left while older than cutoff
            while dq and dq[0].created_at < cutoff:
                dq.popleft()

        # prune by max_items (keep most recent)
        if max_items is not None and len(dq) > max_items:
            # remove from left until size fits
            while len(dq) > max_items:
                dq.popleft()

    def clear_session(self, session_id: str) -> None:
        keys = [k for k in self._store.keys() if k[0] == session_id]
        for k in keys:
            self._store.pop(k, None)
