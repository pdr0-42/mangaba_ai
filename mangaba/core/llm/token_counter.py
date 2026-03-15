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
        if provider == "openai":
            return TokenCounter._count_openai(text, model)
        # Rough heuristic for other providers: ~4 chars per token
        return max(1, len(text) // 4)

    @staticmethod
    def _count_openai(text: str, model: str) -> int:
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
        """Estimate total tokens for a list of chat messages."""
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
        self._records: List[TokenUsage] = []
        self._by_agent: Dict[str, List[TokenUsage]] = {}

    def track(self, usage: TokenUsage, agent_id: Optional[str] = None) -> None:
        if usage.total_tokens <= 0:
            return
        self._records.append(usage)
        if agent_id:
            self._by_agent.setdefault(agent_id, []).append(usage)

    @property
    def total(self) -> TokenUsage:
        t = TokenUsage()
        for u in self._records:
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    def total_for_agent(self, agent_id: str) -> TokenUsage:
        t = TokenUsage()
        for u in self._by_agent.get(agent_id, []):
            t.prompt_tokens += u.prompt_tokens
            t.completion_tokens += u.completion_tokens
            t.total_tokens += u.total_tokens
        return t

    @property
    def call_count(self) -> int:
        return len(self._records)

    def reset(self) -> None:
        self._records.clear()
        self._by_agent.clear()
