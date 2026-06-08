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
    """In-process sliding-window memory.

    This memory implementation keeps the last N interactions in a deque.
    No persistence — when the process ends the memories are gone.

    Attributes:
        max_items: The maximum number of items to store in memory.
        _store: A deque storing memory entries with automatic size limiting.
    """

    def __init__(self, max_items: int = 50) -> None:
        """Initialize the ShortTermMemory.

        Args:
            max_items: The maximum number of items to store (default: 50).
        """
        self.max_items = max_items
        self._store: Deque[Dict[str, Any]] = deque(maxlen=max_items)

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Add a memory entry to the sliding window.

        Args:
            content: The content to store.
            metadata: Optional metadata associated with the content.

        Returns:
            The unique ID of the stored memory entry.
        """
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
        """Perform simple keyword search across stored memories.

        Args:
            query: The search query.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of memory entries sorted by keyword match score.
        """
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
        """Return all stored memories.

        Returns:
            A list of all memory entries in the store.
        """
        return list(self._store)

    def clear(self) -> None:
        """Clear all stored memories."""
        self._store.clear()

    @property
    def size(self) -> int:
        """Return the current number of stored memories.

        Returns:
            The number of items currently in the memory store.
        """
        return len(self._store)
