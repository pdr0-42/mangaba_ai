"""OpenAI provider for LLM integration."""

import json

from typing import Any, List, Dict, Optional, Iterator
from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, FinishReason, ToolCall
from mangaba.core.exceptions import (
    AuthenticationError,
    LLMError,
    RateLimitError,
    RetryableError,
)

from .schemas import _tool_to_openai_schema


class OpenAILLMProvider(BaseLLMProvider):
    name = "openai"
    aliases = ("gpt", "chatgpt")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Initialize the OpenAI LLM provider.

        Args:
            api_key: OpenAI API key.
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini").
            **options: Additional provider-specific options.

        Raises:
            ImportError: If the openai package is not installed.
        """
        super().__init__(api_key, model, **options)
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'openai' not found. Install with: pip install openai"
            ) from exc
        self._client = OpenAI(api_key=api_key)

    def _build_messages(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """Build chat messages from a simple prompt.

        Args:
            prompt: The user prompt.
            system_prompt: Optional system prompt to override the default.

        Returns:
            List of message dictionaries with system prompt (if set) and user message.
        """
        msgs: List[Dict[str, str]] = []
        sp = system_prompt or self._system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from OpenAI.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (temperature, max_output_tokens, system_prompt).

        Returns:
            LLMResponse containing the generated text, usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        try:
            resp = self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenAI error: {exc}", cause=exc) from exc

        text = resp.choices[0].message.content or ""
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
            **kwargs: Additional parameters (temperature, max_output_tokens).

        Returns:
            LLMResponse containing text, tool calls (if any), usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        openai_tools = [_tool_to_openai_schema(t) for t in tools] if tools else None
        try:
            create_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
                "temperature": kwargs.get("temperature", self._temperature),
                "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
            }
            if openai_tools:
                create_kwargs["tools"] = openai_tools
            resp = self._client.chat.completions.create(**create_kwargs)
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenAI error: {exc}", cause=exc) from exc

        msg = resp.choices[0].message
        text = msg.content or ""
        tool_calls: List[ToolCall] = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                args = (
                    json.loads(tc.function.arguments) if tc.function.arguments else {}
                )
                tool_calls.append(
                    ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args)
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
            **kwargs: Additional parameters (temperature, max_output_tokens, system_prompt).

        Yields:
            str: Response tokens as they are generated.

        Raises:
            LLMError: If the streaming request fails.
        """
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=msgs,
                temperature=kwargs.get("temperature", self._temperature),
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content
        except Exception as exc:
            raise LLMError(f"OpenAI streaming error: {exc}", cause=exc) from exc

    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken for accurate OpenAI model tokenization.

        Args:
            text: The text to count tokens for.

        Returns:
            Accurate token count using tiktoken, or rough estimate if tiktoken fails.
        """
        try:
            import tiktoken  # type: ignore

            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except Exception:
            return super().count_tokens(text)

    def _parse_usage(self, resp: Any) -> TokenUsage:
        """Parse token usage from OpenAI response.

        Args:
            resp: The OpenAI API response object.

        Returns:
            TokenUsage object with prompt_tokens, completion_tokens, and total_tokens.
        """
        if resp.usage:
            return TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )
        return TokenUsage()

    def _handle_openai_error(self, exc: Exception) -> None:
        """Convert OpenAI exceptions to Mangaba exceptions.

        Args:
            exc: The original exception from the OpenAI SDK.

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
