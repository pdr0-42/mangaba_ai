"""
Response caching for LLM calls.

Provides in-memory (LRU + TTL) and disk-based (SQLite) caches to avoid
redundant API calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
import time
from abc import ABC, abstractmethod
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, Optional

log = logging.getLogger(__name__)


def _cache_key(prompt: str, config: Dict[str, Any]) -> str:
    """Deterministic hash key from prompt + config."""
    serialised = json.dumps({"prompt": prompt, **config}, sort_keys=True, default=str)
    return hashlib.sha256(serialised.encode()).hexdigest()


# ---------------------------------------------------------------------------
# Abstract cache
# ---------------------------------------------------------------------------

class LLMCache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        ...

    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        ...

    @abstractmethod
    def invalidate(self, key: str) -> None:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...

    # Convenience ---------------------------------------------------------

    def get_or_none(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        return self.get(_cache_key(prompt, config))

    def store(self, prompt: str, config: Dict[str, Any], value: str, ttl: Optional[int] = None) -> None:
        self.set(_cache_key(prompt, config), value, ttl)


# ---------------------------------------------------------------------------
# In-memory LRU + TTL
# ---------------------------------------------------------------------------

class InMemoryCache(LLMCache):
    """Thread-safe in-memory LRU cache with optional TTL (seconds)."""

    def __init__(self, max_size: int = 256, default_ttl: Optional[int] = None) -> None:
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[str, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        with self._lock:
            entry = self._cache.get(key)
            if entry is None:
                return None
            value, expires_at = entry
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                return None
            self._cache.move_to_end(key)
            return value

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expires_at)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)


# ---------------------------------------------------------------------------
# Disk cache (SQLite)
# ---------------------------------------------------------------------------

class DiskCache(LLMCache):
    """Persistent SQLite-based cache."""

    def __init__(self, path: str = ".mangaba_cache.db", default_ttl: Optional[int] = None) -> None:
        self._path = path
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path)

    def get(self, key: str) -> Optional[str]:
        with self._lock, self._connect() as conn:
            row = conn.execute("SELECT value, expires_at FROM cache WHERE key = ?", (key,)).fetchone()
            if row is None:
                return None
            value, expires_at = row
            if expires_at is not None and time.time() > expires_at:
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
                return None
            return value

    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value, expires_at),
            )
            conn.commit()

    def invalidate(self, key: str) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear(self) -> None:
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()
