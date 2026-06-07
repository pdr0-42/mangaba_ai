
"""
LLM provider engine for Mangaba AI v3.0

Supports native function-calling (tool use), streaming, token counting
and a unified response format across Google, OpenAI, Anthropic and
Hugging Face.
"""
from __future__ import annotations

import logging
from typing import Any, List, Iterator, Dict, Optional

from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.types import LLMResponse, TokenUsage
from .providers.constants import _resolve_provider_class


log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# High-level client
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified high-level LLM client with tool use and streaming support."""

    def __init__(self, provider: str, api_key: str, model: str, **options: Any) -> None:
        """Initialize the LLM client with a specific provider.

        Args:
            provider: Provider name (e.g., "google", "openai", "anthropic").
            api_key: API key for the provider service.
            model: Model name/identifier to use.
            **options: Additional provider-specific options (e.g., temperature,
                max_output_tokens, system_prompt).

        Attributes:
            provider_name: The resolved provider name.
            _provider: The underlying provider instance.
            _usage_tracker: List tracking token usage across all calls.
        """
        provider_cls = _resolve_provider_class(provider)
        self.provider_name = provider_cls.name
        self._provider = provider_cls(api_key=api_key, model=model, **options)
        self._usage_tracker: List[TokenUsage] = []

    # -- basic generation ---------------------------------------------------

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from the LLM.

        Emits LLM_START, LLM_END, and LLM_ERROR events to the EventBus.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse containing the generated text, usage metadata, and
            additional information.

        Raises:
            Exception: Propagates any exception from the underlying provider.
        """
        EventBus.emit(Event(event_type=EventType.LLM_START, data={"prompt_preview": prompt[:200], "provider": self.provider_name}))
        try:
            resp = self._provider.generate(prompt, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(Event(event_type=EventType.LLM_END, data={"tokens": resp.usage.total_tokens, "finish_reason": resp.finish_reason.value}))
            return resp
        except Exception as exc:
            EventBus.emit(Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)}))
            raise

    def generate_text(self, prompt: str, **kwargs: Any) -> str:
        """Generate a response and return only the text content.

        Convenience method that returns the text field from the LLMResponse.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional provider-specific parameters.

        Returns:
            The generated text content.
        """
        return self.generate(prompt, **kwargs).text

    # -- tool use -----------------------------------------------------------

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with optional tool/function calling support.

        Emits LLM_START, LLM_END, and LLM_ERROR events to the EventBus with
        tool use metadata.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            tools: Optional list of tool/function definitions for the LLM to use.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse containing the generated text, tool calls (if any),
            usage metadata, and additional information.

        Raises:
            Exception: Propagates any exception from the underlying provider.
        """
        EventBus.emit(Event(
            event_type=EventType.LLM_START,
            data={"mode": "tool_use", "tools_count": len(tools or []), "provider": self.provider_name},
        ))
        try:
            resp = self._provider.generate_with_tools(messages, tools, **kwargs)
            self._track_usage(resp.usage)
            EventBus.emit(Event(
                event_type=EventType.LLM_END,
                data={"tokens": resp.usage.total_tokens, "tool_calls": len(resp.tool_calls), "finish_reason": resp.finish_reason.value},
            ))
            return resp
        except Exception as exc:
            EventBus.emit(Event(event_type=EventType.LLM_ERROR, data={"error": str(exc)}))
            raise

    # -- streaming ----------------------------------------------------------

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream the response token-by-token.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional provider-specific parameters.

        Yields:
            str: Response tokens or chunks as they are generated.
        """
        return self._provider.stream(prompt, **kwargs)

    # -- token counting -----------------------------------------------------

    def count_tokens(self, text: str) -> int:
        """Estimate the token count for the given text.

        Args:
            text: The text to estimate token count for.

        Returns:
            Estimated number of tokens.
        """
        return self._provider.count_tokens(text)

    # -- usage tracking -----------------------------------------------------

    @property
    def total_usage(self) -> TokenUsage:
        """Get the total token usage across all LLM calls.

        Returns:
            TokenUsage object with accumulated prompt_tokens, completion_tokens,
            and total_tokens.
        """
        total = TokenUsage()
        for u in self._usage_tracker:
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.total_tokens += u.total_tokens
        return total

    def _track_usage(self, usage: TokenUsage) -> None:
        """Track token usage from a single LLM call.

        Args:
            usage: TokenUsage object from the LLM response.
        """
        if usage.total_tokens > 0:
            self._usage_tracker.append(usage)
