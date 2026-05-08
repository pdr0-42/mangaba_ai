"""Vector stores for Mangaba AI v3.0"""

from mangaba.vectorstores.base import BaseVectorStore
from mangaba.vectorstores.in_memory import InMemoryVectorStore
<<<<<<< Updated upstream
from mangaba.vectorstores.postgres import PostgresVectorStore
from mangaba.vectorstores.chroma_db import ChromaVectorStore
from mangaba.vectorstores.db_factory import VectorStoreFactory
from mangaba.vectorstores.sqlite import SQLiteVectorStore

__all__ = [
    "BaseVectorStore",
    "InMemoryVectorStore",
    "PostgresVectorStore",
    "ChromaVectorStore",
    "VectorStoreFactory",
    "SQLiteVectorStore",
]
=======
from mangaba.vectorstores.factory import create_vectorstore, get_supported_stores, register_store

__all__ = ["BaseVectorStore", "InMemoryVectorStore", "create_vectorstore", "get_supported_stores", "register_store"]


def __getattr__(name: str):
    if name == "RedisVectorStore":
        from mangaba.vectorstores.redis import RedisVectorStore
        return RedisVectorStore
    if name == "PostgresVectorStore":
        from mangaba.vectorstores.postgres import PostgresVectorStore
        return PostgresVectorStore
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__():
    return list(__all__) + ["RedisVectorStore", "PostgresVectorStore"]
>>>>>>> Stashed changes
