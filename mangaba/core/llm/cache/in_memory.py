"""
In-memory LLM response cache implementation.
"""

from .base import LLMCache
from typing import Optional
from collections import OrderedDict
import threading
import time


class InMemoryCache(LLMCache):
    """Thread-safe in-memory LRU cache with optional TTL (seconds)."""

    def __init__(self, max_size: int = 256, default_ttl: Optional[int] = None) -> None:
        """Initialize the in-memory LRU cache.

        Args:
            max_size: Maximum number of entries to store. Oldest entries are evicted
                when this limit is exceeded (default: 256).
            default_ttl: Default time-to-live in seconds for all entries. None means
                no expiration (default: None).

        Attributes:
            _max_size: Maximum number of entries in the cache.
            _default_ttl: Default TTL for cache entries.
            _cache: OrderedDict storing key -> (value, expires_at) tuples.
            _lock: Threading lock for thread-safe operations.
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, tuple[str, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[str]:
        """Retrieve a value from the cache.

        If the entry exists and is not expired, it is moved to the end of the
        OrderedDict to mark it as recently used (LRU behavior).

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.
        """
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
        """Store a value in the cache.

        If the cache is full, the oldest entry is evicted (LRU behavior).
        If the key already exists, it is updated and moved to the end.

        Args:
            key: The cache key to store under.
            value: The value to cache.
            ttl: Time-to-live in seconds. Uses default_ttl if None (default: None).
        """
        actual_ttl = ttl if ttl is not None else self._default_ttl
        expires_at = time.time() + actual_ttl if actual_ttl else None
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expires_at)
            while len(self._cache) > self._max_size:
                self._cache.popitem(last=False)

    def invalidate(self, key: str) -> None:
        """Remove a specific entry from the cache.

        Args:
            key: The cache key to invalidate.
        """
        with self._lock:
            self._cache.pop(key, None)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def __len__(self) -> int:
        """Return the number of entries currently in the cache.

        Returns:
            The number of cached entries.
        """
        return len(self._cache)
