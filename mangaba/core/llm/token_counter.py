"""
Token counting and usage tracking across providers.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

from mangaba.core.types import TokenUsage

log = logging.getLogger(__name__)


class TokenCounter:
    """Estimate token counts for various providers."""

    @staticmethod
    def count(text: str, provider: str = "openai", model: str = "") -> int:
        """Estimate token count for text using provider-specific tokenization.

        For OpenAI, uses tiktoken library for accurate counts. For other providers,
        uses a rough heuristic (~4 characters per token).

        Args:
            text: The text to count tokens for.
            provider: The provider name (default: "openai").
            model: The model name for provider-specific tokenization (default: "").

        Returns:
            Estimated token count (minimum 1).
        """
        if provider == "openai":
            return TokenCounter._count_openai(text, model)
        # Rough heuristic for other providers: ~4 chars per token
        return max(1, len(text) // 4)

    @staticmethod
    def _count_openai(text: str, model: str) -> int:
        """Count tokens for OpenAI models using tiktoken.

        Args:
            text: The text to count tokens for.
            model: The model name to determine the encoding (default: "gpt-4o-mini").

        Returns:
            Accurate token count using tiktoken, or rough estimate if tiktoken fails.
        """
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.encoding_for_model(model or "gpt-4o-mini")
            return len(enc.encode(text))
        except Exception:
            return max(1, len(text) // 4)

    @staticmethod
    def estimate_messages_tokens(
        messages: List[Dict[str, str]],
        provider: str = "openai",
        model: str = "",
    ) -> int:
        """Estimate total tokens for a list of chat messages.

        Includes overhead for message structure (role, separators, etc.).

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            provider: The provider name (default: "openai").
            model: The model name for provider-specific tokenization (default: "").

        Returns:
            Estimated total token count for all messages including overhead.
        """
        total = 0
        overhead_per_msg = 4  # role + separators
        for msg in messages:
            total += overhead_per_msg
            total += TokenCounter.count(msg.get("content", ""), provider, model)
        total += 2  # start/end tokens
        return total


class UsageTracker:
    """Accumulates token usage across calls, optionally per agent."""

    def __init__(self) -> None:
        """Initialize the usage tracker.

        Attributes:
            _records: List of all TokenUsage records tracked.
            _by_agent: Dictionary mapping agent IDs to their TokenUsage records.
        """
        self._records: List[TokenUsage] = []
        self._by_agent: Dict[str, List[TokenUsage]] = {}

    def track(self, usage: TokenUsage, agent_id: Optional[str] = None) -> None:
        """Track a token usage record.

        Args:
            usage: TokenUsage object to track.
            agent_id: Optional agent ID to associate the usage with.
        """
        if usage.total_tokens <= 0:
            return
        self._records.append(usage)
        if agent_id:
            self._by_agent.setdefault(agent_id, []).append(usage)

    @property
    def total(self) -> TokenUsage:
        """Get the total accumulated token usage across all calls.

        Returns:
            TokenUsage object with accumulated prompt_tokens, completion_tokens,
            and total_tokens.
        """
        t = TokenUsage()
        for u in self._records:
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    def total_for_agent(self, agent_id: str) -> TokenUsage:
        """Get the total token usage for a specific agent.

        Args:
            agent_id: The agent ID to get usage for.

        Returns:
            TokenUsage object with accumulated usage for the specified agent.
        """
        t = TokenUsage()
        for u in self._by_agent.get(agent_id, []):
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    @property
    def call_count(self) -> int:
        """Get the total number of tracked calls.

        Returns:
            Number of usage records tracked.
        """
        return len(self._records)

    def reset(self) -> None:
        """Reset all tracked usage data."""
        self._records.clear()
        self._by_agent.clear()
