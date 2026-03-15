"""Vector stores for Mangaba AI v3.0"""

from mangaba.vectorstores.base import BaseVectorStore
from mangaba.vectorstores.in_memory import InMemoryVectorStore

__all__ = ["BaseVectorStore", "InMemoryVectorStore"]
