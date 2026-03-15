"""
Base memory abstraction for Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMemory(ABC):
    """Abstract memory store that agents can read from and write to."""

    @abstractmethod
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a piece of information. Returns an id."""
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most relevant memories for *query*."""
        ...

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Return every stored memory entry."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Erase all stored memories."""
        ...

    def get_relevant(self, query: str, max_results: int = 5) -> str:
        """Return relevant memories as a formatted string for prompt injection."""
        results = self.search(query, top_k=max_results)
        if not results:
            return ""
        lines = [f"- {r.get('content', '')}" for r in results]
        return "Relevant memories:\n" + "\n".join(lines)
