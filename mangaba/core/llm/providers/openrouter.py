"""OpenRouter provider."""

from typing import Any, Dict, List, Union, Optional

from .openai import OpenAILLMProvider
from mangaba.core.types import LLMResponse, ToolCall, FinishReason
from mangaba.core.exceptions import LLMError
from .schemas import _tool_to_openai_schema


class OpenRouterLLMProvider(OpenAILLMProvider):
    """
    OpenRouter provider implementation for Mangaba AI.
    Handles native fallback routing by formatting the OpenAI SDK payload
    specifically for OpenRouter's requirements.
    """

    name = "openrouter"
    aliases = ("or", "open-router")

    def __init__(
        self, api_key: str, model: Union[str, List[str]], **options: Any
    ) -> None:
        """Initialize the OpenRouter LLM provider.

        OpenRouter provides access to multiple LLM providers through a unified API.
        Supports model fallback routing by accepting a list of models.

        Args:
            api_key: OpenRouter API key.
            model: Model name (string) or list of models for fallback routing.
            **options: Additional provider-specific options (base_url, site_url, site_name).
        """
        # Configuration defaults for the OpenRouter endpoint
        base_url = options.get("base_url") or "https://openrouter.ai/api/v1"
        site_url = options.get("site_url", "https://www.mangaba.ia.br/")
        site_name = options.get("site_name", "Mangaba AI")

        # Initialize base OpenAI provider
        super().__init__(api_key, model, **options)

        from openai import OpenAI

        # Re-initialize the client with OpenRouter's base_url and identity headers
        self._client = OpenAI(
            api_key=api_key,
            base_url=base_url,
            default_headers={
                "HTTP-Referer": site_url,
                "X-Title": site_name,
            },
        )

    def _get_call_params(self, **kwargs: Any) -> Dict[str, Any]:
        """Build API call parameters for OpenRouter.

        Ensures the 'model' is a single string and the fallback list
        is moved to 'extra_body' to satisfy OpenRouter's API requirements.

        Args:
            **kwargs: Additional parameters from the calling method.

        Returns:
            Dictionary of parameters formatted for OpenRouter API.
        """
        # Ensure we have a string for the SDK's 'model' parameter
        if isinstance(self.model, list):
            primary_model = self.model[0]
            # OpenRouter fallback list goes into extra_body.models
            extra_body = kwargs.get("extra_body", {})
            extra_body["models"] = self.model
            kwargs["extra_body"] = extra_body
        else:
            primary_model = self.model

        # Extract standard generation options
        params = {
            "model": primary_model,
            "temperature": kwargs.get("temperature", self._temperature),
            "max_tokens": kwargs.get("max_output_tokens", self._max_tokens),
            "extra_body": kwargs.get("extra_body"),
            "stream": kwargs.get("stream", False),
        }

        # Merge any other extra arguments (like top_p, etc)
        return {k: v for k, v in params.items() if v is not None}

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from OpenRouter.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (temperature, max_output_tokens, system_prompt).

        Returns:
            LLMResponse containing the generated text, usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        # Build standard message format
        messages = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        params = self._get_call_params(**kwargs)

        try:
            # We call the client directly to avoid parent class parameter conflicts
            resp = self._client.chat.completions.create(messages=messages, **params)
            usage = self._parse_usage(resp)
            return LLMResponse(
                content=resp.choices[0].message.content or "",
                usage=usage,
                model=params["model"],
                raw=resp,
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenRouter generation error: {exc}", cause=exc) from exc

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
        # Critical for the ReActEngine to work with fallbacks
        params = self._get_call_params(**kwargs)

        # Convert Mangaba tools to OpenAI-compatible schemas
        if tools:
            params["tools"] = [_tool_to_openai_schema(t) for t in tools]

        try:
            resp = self._client.chat.completions.create(messages=messages, **params)

            msg = resp.choices[0].message
            tool_calls: List[ToolCall] = []

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    import json

                    args = (
                        json.loads(tc.function.arguments)
                        if tc.function.arguments
                        else {}
                    )
                    tool_calls.append(
                        ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args)
                    )

            finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
            usage = self._parse_usage(resp)

            return LLMResponse(
                content=msg.content or "",
                tool_calls=tool_calls,
                usage=usage,
                model=params["model"],
                finish_reason=finish,
                raw=resp,
            )
        except Exception as exc:
            self._handle_openai_error(exc)
            raise LLMError(f"OpenRouter tool-use error: {exc}", cause=exc) from exc
