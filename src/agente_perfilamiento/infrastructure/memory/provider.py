"""
Simple provider to share a singleton MemoryService across nodes.
"""

from typing import Optional

from agente_perfilamiento.application.services.memory_service import MemoryService


_memory_service: Optional[MemoryService] = None


def set_memory_service(service: MemoryService) -> None:
    global _memory_service
    _memory_service = service


def get_memory_service() -> MemoryService:
    if _memory_service is None:
        raise RuntimeError("MemoryService is not initialized. Call set_memory_service() in main before processing.")
    return _memory_service

