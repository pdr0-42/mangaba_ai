"""SQLite vector store implementation for Mangaba AI."""

import sqlite3
import json
import uuid
import math
from typing import List, Dict, Any, Optional
from mangaba.vectorstores import BaseVectorStore


class SQLiteVectorStore(BaseVectorStore):
    """Vector store backed by SQLite with cosine similarity search.

    This implementation stores embeddings as JSON in SQLite and performs
    cosine similarity search in Python.

    Attributes:
        conn: The SQLite database connection.
    """

    def __init__(self, db_path: str = "mangaba_memory.db"):
        """Initialize the SQLiteVectorStore.

        Args:
            db_path: The path to the SQLite database file (default: "mangaba_memory.db").
        """
        self.conn = sqlite3.connect(db_path)
        self._create_table()

    def _create_table(self) -> None:
        """Create the vector store table if it doesn't exist."""
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS vector_store (
                id TEXT PRIMARY KEY, content TEXT, embedding TEXT, metadata TEXT
            )
        """)
        self.conn.commit()

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Store texts with their embeddings in SQLite.

        Args:
            texts: A list of text strings to store.
            embeddings: A list of embedding vectors corresponding to the texts.
            metadatas: Optional list of metadata dictionaries for each text.

        Returns:
            A list of IDs for the stored entries.
        """
        ids = []
        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            meta = json.dumps(metadatas[i] if metadatas else {})
            self.conn.execute(
                "INSERT INTO vector_store VALUES (?, ?, ?, ?)",
                (eid, text, json.dumps(emb), meta),
            )
            ids.append(eid)
        self.conn.commit()
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
        cursor = self.conn.execute(
            "SELECT id, content, embedding, metadata FROM vector_store"
        )
        results = []
        for row in cursor:
            emb = json.loads(row[2])
            score = self._cosine_similarity(query_embedding, emb)
            results.append(
                {
                    "id": row[0],
                    "content": row[1],
                    "score": score,
                    "metadata": json.loads(row[3]),
                }
            )
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            v1: First vector.
            v2: Second vector.

        Returns:
            The cosine similarity score between 0 and 1.
        """
        dot = sum(x * y for x, y in zip(v1, v2))
        mag1 = math.sqrt(sum(x**2 for x in v1))
        mag2 = math.sqrt(sum(x**2 for x in v2))
        return dot / (mag1 * mag2) if mag1 * mag2 != 0 else 0.0

    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID.

        Args:
            ids: A list of IDs to delete.
        """
        self.conn.executemany(
            "DELETE FROM vector_store WHERE id = ?", [(i,) for i in ids]
        )
        self.conn.commit()

    def clear(self) -> None:
        """Remove all entries from the table."""
        self.conn.execute("DELETE FROM vector_store")
        self.conn.commit()

    @property
    def count(self) -> int:
        """Return the number of stored entries.

        Returns:
            The number of entries in the table.
        """
        return self.conn.execute("SELECT COUNT(*) FROM vector_store").fetchone()[0]
