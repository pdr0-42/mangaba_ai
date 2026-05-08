"""
PostgreSQL vector store using pgvector extension for vector similarity search.

Requires PostgreSQL server with pgvector extension enabled.
Install with: pip install mangaba[postgres]
"""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore

try:
    import psycopg
    from psycopg.rows import dict_row
    from psycopg.types.json import Jsonb
    POSTGRES_AVAILABLE = True
except ImportError:
    psycopg = None
    dict_row = None
    Jsonb = None
    POSTGRES_AVAILABLE = False


class PostgresVectorStore(BaseVectorStore):
    """Vector store backed by PostgreSQL with pgvector extension."""

    def __init__(
        self,
        url: str | None = None,
        table_name: str = "mangaba_vectors",
        vector_dimensions: int = 1536,
        create_table: bool = True,
        **kwargs: Any,
    ) -> None:
        if psycopg is None:
            raise ImportError(
                "psycopg package is required. Install with: pip install mangaba[postgres]"
            )

        resolved_url = url or os.getenv("MANGABA_VECTORSTORE_URL") or os.getenv("DATABASE_URL")
        if not resolved_url:
            raise ValueError(
                "PostgreSQL connection URL is required. "
                "Pass it as 'url' parameter or set MANGABA_VECTORSTORE_URL / DATABASE_URL env var."
            )

        self._table_name = table_name
        self._vector_dimensions = vector_dimensions
        self._conn: psycopg.Connection = psycopg.connect(resolved_url, row_factory=dict_row, **kwargs)

        if create_table:
            self._ensure_table()

    def _ensure_table(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {self._table_name} (
                    id VARCHAR(12) PRIMARY KEY,
                    text TEXT NOT NULL,
                    embedding VECTOR({self._vector_dimensions}),
                    metadata JSONB DEFAULT '{{}}'
                )
            """)
            cur.execute(f"""
                CREATE INDEX IF NOT EXISTS {self._table_name}_embedding_idx
                ON {self._table_name}
                USING hnsw (embedding vector_cosine_ops)
            """)
        self._conn.commit()

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        ids: List[str] = []
        rows = []

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}
            rows.append((eid, text, emb, metadata))
            ids.append(eid)

        with self._conn.cursor() as cur:
            for eid, text, emb, metadata in rows:
                metadata_value = Jsonb(metadata) if Jsonb is not None else metadata
                cur.execute(
                    f"INSERT INTO {self._table_name} (id, text, embedding, metadata) VALUES (%s, %s, %s::vector, %s::jsonb)",
                    (eid, text, json.dumps(emb), metadata_value),
                )
        self._conn.commit()
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        emb_str = json.dumps(query_embedding)
        with self._conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, text, metadata,
                       1 - (embedding <=> %s::vector) AS score
                FROM {self._table_name}
                ORDER BY embedding <=> %s::vector
                LIMIT %s
                """,
                (emb_str, emb_str, top_k),
            )
            rows = cur.fetchall()

        output = []
        for row in rows:
            metadata = row["metadata"] if isinstance(row["metadata"], dict) else {}
            output.append({
                "id": row["id"],
                "content": row["text"],
                "score": float(row["score"]),
                "metadata": metadata,
            })

        return output

    def delete(self, ids: List[str]) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table_name} WHERE id = ANY(%s)",
                (ids,),
            )
        self._conn.commit()

    def clear(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self._table_name}")
        self._conn.commit()

    @property
    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._table_name}")
            return cur.fetchone()["count"]

    def close(self) -> None:
        self._conn.close()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass
