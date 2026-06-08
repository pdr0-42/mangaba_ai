"""
LLM Cache Base Module

This module defines the abstract base class for LLM response caching implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import hashlib
import json


class LLMCache(ABC):
    """Abstract base class for LLM response caching implementations."""

    @staticmethod
    def _cache_key(prompt: str, config: Dict[str, Any]) -> str:
        """Generate a deterministic cache key from prompt and configuration.

        Args:
            prompt: The input prompt string.
            config: Configuration dictionary including model, temperature, etc.

        Returns:
            A SHA256 hash string that uniquely identifies the prompt+config combination.
        """
        serialised = json.dumps(
            {"prompt": prompt, **config}, sort_keys=True, default=str
        )
        return hashlib.sha256(serialised.encode()).hexdigest()

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        """Retrieve a cached value by key.

        Args:
            key: The cache key to look up.

        Returns:
            The cached value if found and not expired, None otherwise.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("get() must be implemented by subclass")

    @abstractmethod
    def set(self, key: str, value: str, ttl: Optional[int] = None) -> None:
        """Store a value in the cache with an optional TTL.

        Args:
            key: The cache key to store under.
            value: The value to cache.
            ttl: Time-to-live in seconds. None means no expiration.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("set() must be implemented by subclass")

    @abstractmethod
    def invalidate(self, key: str) -> None:
        """Remove a specific entry from the cache.

        Args:
            key: The cache key to invalidate.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("invalidate() must be implemented by subclass")

    @abstractmethod
    def clear(self) -> None:
        """Clear all entries from the cache.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("clear() must be implemented by subclass")

    # Convenience ---------------------------------------------------------

    def get_or_none(self, prompt: str, config: Dict[str, Any]) -> Optional[str]:
        """Get a cached response by prompt and configuration.

        Convenience method that generates the cache key from prompt and config.

        Args:
            prompt: The input prompt string.
            config: Configuration dictionary including model, temperature, etc.

        Returns:
            The cached response if found and not expired, None otherwise.
        """
        return self.get(self._cache_key(prompt, config))

    def store(
        self, prompt: str, config: Dict[str, Any], value: str, ttl: Optional[int] = None
    ) -> None:
        """Store a response in the cache by prompt and configuration.

        Convenience method that generates the cache key from prompt and config.

        Args:
            prompt: The input prompt string.
            config: Configuration dictionary including model, temperature, etc.
            value: The response value to cache.
            ttl: Time-to-live in seconds. None means no expiration.
        """
        self.set(self._cache_key(prompt, config), value, ttl)
