"""
Application service for user entity memory (profile-like attributes).
"""

from typing import Dict

from agente_perfilamiento.application.ports.entity_memory_repository import (
    EntityMemoryRepository,
)


class EntityMemoryService:
    def __init__(self, repository: EntityMemoryRepository) -> None:
        self._repo = repository

    def get(self, user_id: str) -> Dict:
        return self._repo.get(user_id)

    def upsert(self, user_id: str, attributes: Dict) -> None:
        # Shallow merge by default
        current = self._repo.get(user_id)
        merged = {**current, **(attributes or {})}
        self._repo.upsert(user_id, merged)

    def clear(self, user_id: str) -> None:
        self._repo.clear(user_id)

