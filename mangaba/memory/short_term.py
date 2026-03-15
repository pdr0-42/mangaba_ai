"""
Short-term (sliding window) memory for Mangaba AI v3.0

Keeps the last *N* interactions in a list. No persistence — when the
process ends the memories are gone.
"""

from __future__ import annotations

import uuid
from collections import deque
from datetime import datetime
from typing import Any, Deque, Dict, List, Optional

from mangaba.memory.base import BaseMemory


class ShortTermMemory(BaseMemory):
    """In-process sliding-window memory."""

    def __init__(self, max_items: int = 50) -> None:
        self.max_items = max_items
        self._store: Deque[Dict[str, Any]] = deque(maxlen=max_items)

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        entry_id = uuid.uuid4().hex[:12]
        entry: Dict[str, Any] = {
            "id": entry_id,
            "content": content,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat(),
        }
        self._store.append(entry)
        return entry_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Simple keyword search across stored memories."""
        q_lower = query.lower()
        scored = []
        for entry in self._store:
            text = entry["content"].lower()
            # Score = number of query words found in the content
            score = sum(1 for w in q_lower.split() if w in text)
            if score > 0:
                scored.append((score, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:top_k]]

    def get_all(self) -> List[Dict[str, Any]]:
        return list(self._store)

    def clear(self) -> None:
        self._store.clear()

    @property
    def size(self) -> int:
        return len(self._store)
