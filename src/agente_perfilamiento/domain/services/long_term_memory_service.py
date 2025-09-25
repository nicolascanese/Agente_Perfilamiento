"""
Application service for long-term memory summaries.
"""

from typing import Dict, List

from agente_perfilamiento.ports.long_term_memory_repository import (
    LongTermMemoryRepository,
)


class LongTermMemoryService:
    def __init__(self, repository: LongTermMemoryRepository) -> None:
        self._repo = repository

    def save_summary(self, record: Dict) -> str:
        return self._repo.save_summary(record)

    def list_user_summaries(self, user_id: str) -> List[Dict]:
        return self._repo.list_user_summaries(user_id)

    def get_user_summaries_text(self, user_id: str) -> str:
        return self._repo.read_user_summaries_text(user_id)
