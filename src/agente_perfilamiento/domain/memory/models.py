"""
Domain models for short-term memory handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ShortTermMemoryItem:
    agent_name: str
    session_id: str
    role: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class MemoryWindow:
    items: List[ShortTermMemoryItem]
