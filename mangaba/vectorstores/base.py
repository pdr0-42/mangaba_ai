"""
Base vector store abstraction for Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """Abstract vector store for embedding-based similarity search."""

    @abstractmethod
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]:
        """Store texts with their embeddings. Returns list of IDs."""
        ...

    @abstractmethod
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Find the *top_k* most similar entries. Returns list of {id, content, score, metadata}."""
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries."""
        ...

    @property
    @abstractmethod
    def count(self) -> int:
        """Number of stored entries."""
        ...
