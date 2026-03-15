"""
Base embedding abstraction for Mangaba AI v3.0
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List


class BaseEmbedding(ABC):
    """Abstract interface for text embedding providers."""

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Return the embedding vector for a single text."""
        ...

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts. Default: call embed_text in a loop."""
        return [self.embed_text(t) for t in texts]

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the embedding vectors."""
        ...
