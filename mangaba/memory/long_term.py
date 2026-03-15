"""
Long-term memory backed by SQLite for Mangaba AI v3.0

Persists memories to disk and supports optional vector-similarity search
when an embedding provider is available (falls back to keyword search).
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from mangaba.memory.base import BaseMemory


_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    content TEXT NOT NULL,
    metadata TEXT DEFAULT '{}',
    embedding TEXT DEFAULT NULL,
    created_at TEXT NOT NULL
);
"""


class LongTermMemory(BaseMemory):
    """SQLite-backed persistent memory with optional embedding search."""

    def __init__(
        self,
        db_path: str = "mangaba_memory.db",
        embedding_fn: Optional[Any] = None,
    ) -> None:
        self.db_path = db_path
        self.embedding_fn = embedding_fn  # callable(text) -> List[float]
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.execute(_CREATE_TABLE)
        self._conn.commit()

    # ── public API ─────────────────────────────────────────────────────

    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        entry_id = uuid.uuid4().hex[:12]
        embedding_json: Optional[str] = None
        if self.embedding_fn:
            vec = self.embedding_fn(content)
            embedding_json = json.dumps(vec)

        self._conn.execute(
            "INSERT INTO memories (id, content, metadata, embedding, created_at) VALUES (?, ?, ?, ?, ?)",
            (entry_id, content, json.dumps(metadata or {}), embedding_json, datetime.now().isoformat()),
        )
        self._conn.commit()
        return entry_id

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if self.embedding_fn:
            return self._vector_search(query, top_k)
        return self._keyword_search(query, top_k)

    def get_all(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT id, content, metadata, created_at FROM memories ORDER BY created_at DESC").fetchall()
        return [self._row_to_dict(r) for r in rows]

    def clear(self) -> None:
        self._conn.execute("DELETE FROM memories")
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    # ── internals ──────────────────────────────────────────────────────

    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT id, content, metadata, created_at FROM memories").fetchall()
        q_lower = query.lower()
        scored = []
        for r in rows:
            text = r[1].lower()
            score = sum(1 for w in q_lower.split() if w in text)
            if score > 0:
                scored.append((score, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_dict(r) for _, r in scored[:top_k]]

    def _vector_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        query_vec = self.embedding_fn(query)
        rows = self._conn.execute("SELECT id, content, metadata, created_at, embedding FROM memories WHERE embedding IS NOT NULL").fetchall()
        scored = []
        for r in rows:
            vec = json.loads(r[4])
            sim = self._cosine_similarity(query_vec, vec)
            scored.append((sim, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [self._row_to_dict(r[:4]) for _, r in scored[:top_k]]

    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        if len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @staticmethod
    def _row_to_dict(row: tuple) -> Dict[str, Any]:
        return {
            "id": row[0],
            "content": row[1],
            "metadata": json.loads(row[2]) if row[2] else {},
            "created_at": row[3],
        }
