"""
File-based implementation of long-term memory repository (summaries),
compatible with the external repo pattern.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from agente_perfilamiento.application.ports.long_term_memory_repository import (
    LongTermMemoryRepository,
)
from agente_perfilamiento.infrastructure.config.settings import settings


class FileLongTermMemoryRepository(LongTermMemoryRepository):
    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = Path(base_dir) if base_dir else Path(settings.memory_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _user_files(self, user_id: str) -> List[Path]:
        pattern = f"{user_id}_*.json"
        return sorted(self.base_dir.glob(pattern))

    def save_summary(self, record: Dict) -> str:
        user_id = str(record.get("id_user", "unknown"))
        session_id = str(record.get("id_conversacion", ""))
        fecha_inicio = str(record.get("fecha_inicio", ""))
        timestamp = datetime.now().strftime("%Y%m%d")

        # Filename format similar to external repo: user_YYYYMMDD<session>.json
        filename = f"{user_id}_{timestamp}{session_id}.json"
        path = self.base_dir / filename
        with path.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False, indent=2)
        return str(path)

    def list_user_summaries(self, user_id: str) -> List[Dict]:
        result: List[Dict] = []
        for p in self._user_files(user_id):
            try:
                with p.open("r", encoding="utf-8") as f:
                    result.append(json.load(f))
            except Exception:
                continue
        return result

    def read_user_summaries_text(self, user_id: str) -> str:
        blocks: List[str] = []
        for rec in self.list_user_summaries(user_id):
            resumen = rec.get("resumen") or rec.get("summary") or ""
            if resumen:
                blocks.append(resumen)
        return "\n\n---\n\n".join(blocks)

