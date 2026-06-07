

"""
Disk-based LLM response cache using SQLite.
"""

from .base import LLMCache
from typing import Optional
import sqlite3
import threading
import time

class DiskCache(LLMCache):
    """Persistent SQLite-based cache."""

    def __init__(self, path: str = ".mangaba_cache.db", default_ttl: Optional[int] = None) -> None:
        """Initialize the disk-based SQLite cache.

        Args:
            path: Path to the SQLite database file (default: ".mangaba_cache.db").
            default_ttl: Default time-to-live in seconds for all entries. None means
                no expiration (default: None).

        Attributes:
            _path: Path to the SQLite database file.
            _default_ttl: Default TTL for cache entries.
            _lock: Threading lock for thread-safe operations.
        """
        self._path = path
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize the SQLite database schema.

        Creates the cache table if it does not exist.
        """
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS cache "
                "(key TEXT PRIMARY KEY, value TEXT, expires_at REAL)"
            )
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        """Create a new SQLite connection.

        Returns:
            A sqlite3.Connection object for the database.
        """
        return sqlite3.connect(self._path)

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value from the disk cache.

        Expired entries are automatically deleted from the database.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
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
        """Store a value in the disk cache.

        Args:
            key: The cache key to store under.
            value: The value to cache.
            ttl: Time-to-live in seconds. Uses default_ttl if None (default: None).
        """
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock, self._connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, expires_at) VALUES (?, ?, ?)",
                (key, value, expires_at),
            )
            conn.commit()

    def invalidate(self, key: str) -> None:
        """Remove a specific entry from the disk cache.

        Args:
            key: The cache key to invalidate.
        """
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()

    def clear(self) -> None:
        """Remove all entries from the disk cache."""
        with self._lock, self._connect() as conn:
            conn.execute("DELETE FROM cache")
            conn.commit()