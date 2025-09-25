"""
File-based entity memory repository storing per-user JSON profiles.
"""

import json
from pathlib import Path
from typing import Dict

from agente_perfilamiento.ports.entity_memory_repository import (
    EntityMemoryRepository,
)
from agente_perfilamiento.infrastructure.config.settings import settings


class FileEntityMemoryRepository(EntityMemoryRepository):
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(settings.memory_dir) / "entities"
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, user_id: str) -> Path:
        return self.base_dir / f"{user_id}.json"

    def get(self, user_id: str) -> Dict:
        path = self._path(user_id)
        if not path.exists():
            return {}
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def upsert(self, user_id: str, attributes: Dict) -> None:
        path = self._path(user_id)
        with path.open("w", encoding="utf-8") as f:
            json.dump(attributes or {}, f, ensure_ascii=False, indent=2)

    def clear(self, user_id: str) -> None:
        path = self._path(user_id)
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
