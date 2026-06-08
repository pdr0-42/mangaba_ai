"""Abstract base class for LLM providers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple

from mangaba.core.types import LLMResponse


class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    name: str = "base"
    aliases: Tuple[str, ...] = ()

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Initialize the LLM provider.

        Args:
            api_key: API key for the provider service.
            model: Model name/identifier to use.
            **options: Additional provider-specific options (e.g., temperature,
                max_output_tokens, system_prompt).

        Attributes:
            api_key: The API key for authentication.
            model: The model name/identifier.
            options: Dictionary of additional options.
            _temperature: Temperature for generation (default: 0.7).
            _max_tokens: Maximum tokens in output (default: 1024).
            _system_prompt: Optional system prompt to use.
        """
        self.api_key = api_key
        self.model = model
        self.options = options or {}
        self._temperature = options.get("temperature", 0.7)
        self._max_tokens = options.get("max_output_tokens", 1024)
        self._system_prompt = options.get("system_prompt")

    @classmethod
    def matches(cls, provider_name: str) -> bool:
        """Check if the provider name matches this provider.

        Args:
            provider_name: The provider name to check (case-insensitive).

        Returns:
            True if the provider name matches this provider's name or aliases,
            False otherwise.
        """
        n = provider_name.lower()
        return n == cls.name or n in cls.aliases

    # -- public API ----------------------------------------------------------

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from the LLM.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse containing the generated text, usage metadata, and
            additional information.

        Raises:
            NotImplementedError: This method must be implemented by subclasses.
        """
        raise NotImplementedError("generate() must be implemented by subclass")

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with optional tool/function calling support.

        This default implementation extracts user content from messages and
        falls back to plain generate(). Subclasses should override this to
        implement native tool calling support.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            tools: Optional list of tool/function definitions for the LLM to use.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse containing the generated text, tool calls (if any),
            usage metadata, and additional information.
        """
        # Default: ignore tools and fall back to plain generate
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content = m.get("content", "")
        return self.generate(user_content, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream the response token-by-token.

        This default implementation generates the full response and yields it
        as a single chunk. Subclasses should override this to implement true
        token-by-token streaming.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional provider-specific parameters.

        Yields:
            str: Response tokens or chunks as they are generated.
        """
        resp = self.generate(prompt, **kwargs)
        yield resp.text

    def count_tokens(self, text: str) -> int:
        """Estimate the token count for the given text.

        This default implementation uses a rough word-based estimate
        (approximately 4 characters per token). Subclasses should override
        this to use provider-specific tokenizers for accurate counts.

        Args:
            text: The text to estimate token count for.

        Returns:
            Estimated number of tokens (minimum 1).
        """
        return max(1, len(text) // 4)
