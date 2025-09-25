"""
Application port for long-term memory (summaries) repository.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class LongTermMemoryRepository(ABC):
    @abstractmethod
    def save_summary(self, record: Dict) -> str:  # returns file path or id
        ...

    @abstractmethod
    def list_user_summaries(self, user_id: str) -> List[Dict]:
        ...

    @abstractmethod
    def read_user_summaries_text(self, user_id: str) -> str:
        ...

