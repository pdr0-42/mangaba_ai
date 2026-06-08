"""
Base vector store abstraction for Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseVectorStore(ABC):
    """Abstract vector store for embedding-based similarity search.

    This base class defines the interface for all vector store implementations,
    providing methods for storing, searching, and managing vector embeddings.
    """

    @abstractmethod
    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Store texts with their embeddings.

        Args:
            texts: A list of text strings to store.
            embeddings: A list of embedding vectors corresponding to the texts.
            metadatas: Optional list of metadata dictionaries for each text.

        Returns:
            A list of IDs for the stored entries.
        """
        ...

    @abstractmethod
    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Find the most similar entries to the query embedding.

        Args:
            query_embedding: The query embedding vector.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of dictionaries containing id, content, score, and metadata
            for each result.
        """
        ...

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID.

        Args:
            ids: A list of IDs to delete.
        """
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all entries from the vector store."""
        ...

    @property
    @abstractmethod
    def count(self) -> int:
        """Return the number of stored entries.

        Returns:
            The number of entries in the vector store.
        """
        ...
