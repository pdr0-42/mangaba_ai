"""
Base memory abstraction for Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseMemory(ABC):
    """Abstract memory store that agents can read from and write to.

    This base class defines the interface for all memory implementations,
    providing methods for storing, retrieving, and managing memory entries.
    """

    @abstractmethod
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """Store a piece of information in memory.

        Args:
            content: The content to store in memory.
            metadata: Optional metadata associated with the content.

        Returns:
            A unique identifier for the stored memory entry.
        """
        ...

    @abstractmethod
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Retrieve the most relevant memories for a query.

        Args:
            query: The search query to find relevant memories.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of memory entries, each as a dictionary containing
            content and metadata.
        """
        ...

    @abstractmethod
    def get_all(self) -> List[Dict[str, Any]]:
        """Return every stored memory entry.

        Returns:
            A list of all memory entries in the memory store.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Erase all stored memories."""
        ...

    def get_relevant(self, query: str, max_results: int = 5) -> str:
        """Return relevant memories as a formatted string for prompt injection.

        Args:
            query: The search query to find relevant memories.
            max_results: The maximum number of results to return (default: 5).

        Returns:
            A formatted string containing relevant memories, or an empty
            string if no relevant memories are found.
        """
        results = self.search(query, top_k=max_results)
        if not results:
            return ""
        lines = [f"- {r.get('content', '')}" for r in results]
        return "Relevant memories:\n" + "\n".join(lines)
