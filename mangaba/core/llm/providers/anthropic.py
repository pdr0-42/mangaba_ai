"""Anthropic provider for LLM integration."""

from typing import Any, Dict, Iterator, List, Optional


from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, ToolCall, FinishReason
from mangaba.core.exceptions import (
    LLMError,
    AuthenticationError,
    RateLimitError,
    RetryableError,
)

from .schemas import _tool_to_anthropic_schema


class AnthropicLLMProvider(BaseLLMProvider):
    name = "anthropic"
    aliases = ("claude",)

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Initialize the Anthropic LLM provider.

        Args:
            api_key: Anthropic API key.
            model: Model name (e.g., "claude-3-haiku", "claude-3-opus").
            **options: Additional provider-specific options.

        Raises:
            ImportError: If the anthropic package is not installed.
        """
        super().__init__(api_key, model, **options)
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'anthropic' not found. Install with: pip install anthropic"
            ) from exc
        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from Anthropic Claude.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (max_output_tokens, temperature, system_prompt).

        Returns:
            LLMResponse containing the generated text, usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        try:
            resp = self._client.messages.create(
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                system=kwargs.get("system_prompt", self._system_prompt) or "",
                messages=[{"role": "user", "content": prompt}],
            )
        except Exception as exc:
            self._handle_anthropic_error(exc)
            raise LLMError(f"Anthropic error: {exc}", cause=exc) from exc

        parts = [
            getattr(b, "text", "")
            for b in resp.content
            if getattr(b, "type", "") == "text"
        ]
        text = "\n".join(p for p in parts if p)
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with tool/function calling support.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            tools: Optional list of tool definitions for function calling.
            **kwargs: Additional parameters (max_output_tokens, temperature).

        Returns:
            LLMResponse containing text, tool calls (if any), usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        anthropic_tools = (
            [_tool_to_anthropic_schema(t) for t in tools] if tools else None
        )
        # Extract system from messages
        system_text = ""
        api_messages = []
        for m in messages:
            if m["role"] == "system":
                system_text = m.get("content", "")
            else:
                api_messages.append(m)

        try:
            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
                "temperature": kwargs.get("temperature", self._temperature),
                "messages": api_messages,
            }
            if system_text:
                create_kwargs["system"] = system_text
            if anthropic_tools:
                create_kwargs["tools"] = anthropic_tools

            resp = self._client.messages.create(**create_kwargs)
        except Exception as exc:
            self._handle_anthropic_error(exc)
            raise LLMError(f"Anthropic error: {exc}", cause=exc) from exc

        text = ""
        tool_calls: List[ToolCall] = []
        for block in resp.content:
            if getattr(block, "type", "") == "text":
                text += getattr(block, "text", "")
            elif getattr(block, "type", "") == "tool_use":
                tool_calls.append(
                    ToolCall(
                        id=block.id,
                        tool_name=block.name,
                        arguments=block.input if isinstance(block.input, dict) else {},
                    )
                )

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=finish,
            raw=resp,
        )

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream the response token-by-token.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (max_output_tokens, temperature, system_prompt).

        Yields:
            str: Response tokens as they are generated.

        Raises:
            LLMError: If the streaming request fails.
        """
        try:
            with self._client.messages.stream(
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                system=kwargs.get("system_prompt", self._system_prompt) or "",
                messages=[{"role": "user", "content": prompt}],
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as exc:
            raise LLMError(f"Anthropic streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, resp: Any) -> TokenUsage:
        """Parse token usage from Anthropic response.

        Args:
            resp: The Anthropic API response object.

        Returns:
            TokenUsage object with prompt_tokens, completion_tokens, and total_tokens.
        """
        if hasattr(resp, "usage") and resp.usage:
            return TokenUsage(
                prompt_tokens=getattr(resp.usage, "input_tokens", 0),
                completion_tokens=getattr(resp.usage, "output_tokens", 0),
                total_tokens=getattr(resp.usage, "input_tokens", 0)
                + getattr(resp.usage, "output_tokens", 0),
            )
        return TokenUsage()

    def _handle_anthropic_error(self, exc: Exception) -> None:
        """Convert Anthropic exceptions to Mangaba exceptions.

        Args:
            exc: The original exception from the Anthropic SDK.

        Raises:
            AuthenticationError: If authentication fails.
            RateLimitError: If rate limit is exceeded.
            RetryableError: If the error is retryable (timeout, connection).
        """
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc
