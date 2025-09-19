"""
Application port for entity (user profile) memory repository.
"""

from abc import ABC, abstractmethod
from typing import Dict


class EntityMemoryRepository(ABC):
    @abstractmethod
    def get(self, user_id: str) -> Dict:
        ...

    @abstractmethod
    def upsert(self, user_id: str, attributes: Dict) -> None:
        ...

    @abstractmethod
    def clear(self, user_id: str) -> None:
        ...

