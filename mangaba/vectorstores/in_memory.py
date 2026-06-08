"""
In-memory vector store using pure Python cosine similarity.

No external dependencies — suitable as a default when numpy/faiss
are not installed.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore


class InMemoryVectorStore(BaseVectorStore):
    """Simple in-process vector store backed by a Python list.

    This implementation uses pure Python cosine similarity and requires no
    external dependencies, making it suitable as a default when numpy/faiss
    are not installed.

    Attributes:
        _entries: A list of dictionaries containing id, text, embedding, and metadata.
    """

    def __init__(self) -> None:
        """Initialize the InMemoryVectorStore."""
        self._entries: List[Dict[str, Any]] = []  # {id, text, embedding, metadata}

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Store texts with their embeddings in memory.

        Args:
            texts: A list of text strings to store.
            embeddings: A list of embedding vectors corresponding to the texts.
            metadatas: Optional list of metadata dictionaries for each text.

        Returns:
            A list of IDs for the stored entries.
        """
        ids: List[str] = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            self._entries.append(
                {
                    "id": eid,
                    "text": text,
                    "embedding": emb,
                    "metadata": (
                        metadatas[i] if metadatas and i < len(metadatas) else {}
                    ),
                }
            )
            ids.append(eid)
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar entries using cosine similarity.

        Args:
            query_embedding: The query embedding vector.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of dictionaries containing id, content, score, and metadata
            for each result, sorted by similarity score.
        """
        scored = []
        for entry in self._entries:
            sim = _cosine_similarity(query_embedding, entry["embedding"])
            scored.append((sim, entry))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "id": e["id"],
                "content": e["text"],
                "score": s,
                "metadata": e["metadata"],
            }
            for s, e in scored[:top_k]
        ]

    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID.

        Args:
            ids: A list of IDs to delete.
        """
        id_set = set(ids)
        self._entries = [e for e in self._entries if e["id"] not in id_set]

    def clear(self) -> None:
        """Remove all entries from the store."""
        self._entries.clear()

    @property
    def count(self) -> int:
        """Return the number of stored entries.

        Returns:
            The number of entries in the store.
        """
        return len(self._entries)


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Args:
        a: First vector.
        b: Second vector.

    Returns:
        The cosine similarity score between 0 and 1.
    """
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
