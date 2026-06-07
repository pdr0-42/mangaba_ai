"""Hugging Face Inference API provider."""

import json
from typing import Any, Dict, Iterator, List, Optional, Tuple

from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.exceptions import LLMError
from mangaba.core.types import FinishReason, LLMResponse, TokenUsage, ToolCall
from .schemas import _tools_to_hf_prompt_section


def list_huggingface_models(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return curated HuggingFace open models, optionally filtered by category.

    Args:
        category: Optional category filter (general, code, reasoning, embedding).

    Returns:
        List of model dictionaries with metadata (id, name, category, context, etc.).
    """
    from .constants import HF_OPEN_MODELS

    if category:
        return [m for m in HF_OPEN_MODELS if m["category"] == category]
    return list(HF_OPEN_MODELS)


def hf_model_supports_tools(model_id: str) -> bool:
    """Check if a model supports native function calling via chat_completion.

    Args:
        model_id: The HuggingFace model ID to check.

    Returns:
        True if the model supports native function calling, False otherwise.
    """
    from .constants import _HF_NATIVE_TOOL_MODELS

    return model_id in _HF_NATIVE_TOOL_MODELS


class HuggingFaceLLMProvider(BaseLLMProvider):
    """Hugging Face Inference API. Uses prompt-engineering for tool use."""

    name = "huggingface"
    aliases = ("hf", "hugging-face")

    @property
    def SUPPORTED_MODELS(self) -> Tuple[str, ...]:
        """Supported models excluding embeddings."""
        from .constants import HF_OPEN_MODELS

        return tuple(m["id"] for m in HF_OPEN_MODELS if m["category"] != "embedding")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Initialize the HuggingFace Inference API provider.

        Args:
            api_key: HuggingFace API token.
            model: Model ID (e.g., "mistralai/Mistral-7B-Instruct-v0.3").
            **options: Additional provider-specific options.

        Raises:
            ImportError: If the huggingface-hub package is not installed.
        """
        super().__init__(api_key, model, **options)
        try:
            from huggingface_hub import InferenceClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'huggingface-hub' not found. Install with: pip install huggingface-hub"
            ) from exc
        self._client = InferenceClient(token=api_key)

    @classmethod
    def list_models(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return curated open models available via HuggingFace Inference API.

        Args:
            category: Optional category filter (general, code, reasoning, embedding).

        Returns:
            List of model dictionaries with metadata.
        """
        return list_huggingface_models(category=category)

    def _chat_messages(self, prompt: str) -> List[Dict[str, str]]:
        """Build chat messages from a simple prompt.

        Args:
            prompt: The user prompt.

        Returns:
            List of message dictionaries with system prompt (if set) and user message.
        """
        msgs: List[Dict[str, str]] = []
        if self._system_prompt:
            msgs.append({"role": "system", "content": self._system_prompt})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from HuggingFace Inference API.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (max_output_tokens, temperature).

        Returns:
            LLMResponse containing the generated text, usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        try:
            response = self._client.chat_completion(
                messages=self._chat_messages(prompt),
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        choice = response.choices[0]
        text = choice.message.content or ""
        usage = getattr(response, "usage", None)
        token_usage = (
            TokenUsage(
                prompt_tokens=getattr(usage, "prompt_tokens", 0),
                completion_tokens=getattr(usage, "completion_tokens", 0),
                total_tokens=getattr(usage, "total_tokens", 0),
            )
            if usage
            else TokenUsage()
        )
        return LLMResponse(
            content=text, model=self.model, usage=token_usage, raw=response
        )

    def _supports_native_tools(self) -> bool:
        """Check if the current model supports native function calling.

        Returns:
            True if the model supports native function calling, False otherwise.
        """
        return hf_model_supports_tools(self.model)

    def _openai_tool_schema(self, tool: Any) -> Dict[str, Any]:
        """Convert a tool to OpenAI-compatible function schema format.

        Args:
            tool: A BaseTool instance with get_function_schema() method.

        Returns:
            Dictionary in OpenAI function calling format.
        """
        schema = tool.get_function_schema()
        return {
            "type": "function",
            "function": {
                "name": schema["name"],
                "description": schema["description"],
                "parameters": schema.get(
                    "parameters", {"type": "object", "properties": {}}
                ),
            },
        }

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with tool/function calling support.

        Uses native function calling if the model supports it, otherwise falls back
        to prompt-based tool calling by injecting tool descriptions into the system message.

        Args:
            messages: List of message dictionaries with 'role' and 'content' keys.
            tools: Optional list of tool definitions for function calling.
            **kwargs: Additional parameters (max_output_tokens, temperature).

        Returns:
            LLMResponse containing text, tool calls (if any), usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        tool_list = tools or []

        if self._supports_native_tools() and tool_list:
            # Native function calling via chat_completion tools parameter
            hf_tools = [self._openai_tool_schema(t) for t in tool_list]
            try:
                response = self._client.chat_completion(
                    messages=messages,
                    model=self.model,
                    tools=hf_tools,
                    max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                    temperature=kwargs.get("temperature", self._temperature),
                )
            except Exception as exc:
                raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

            choice = response.choices[0]
            native_calls = getattr(choice.message, "tool_calls", None) or []
            if native_calls:
                tool_calls = [
                    ToolCall(
                        tool_name=c.function.name,
                        arguments=json.loads(c.function.arguments)
                        if isinstance(c.function.arguments, str)
                        else c.function.arguments,
                    )
                    for c in native_calls
                ]
                return LLMResponse(
                    content=choice.message.content or "",
                    tool_calls=tool_calls,
                    model=self.model,
                    finish_reason=FinishReason.TOOL_CALLS,
                    raw=response,
                )
            return LLMResponse(
                content=choice.message.content or "", model=self.model, raw=response
            )

        # Fallback: inject tool descriptions into system message (prompt-based)
        tool_section = _tools_to_hf_prompt_section(tool_list)
        enriched: List[Dict[str, Any]] = []
        injected = False
        for m in messages:
            if m.get("role") == "system" and tool_section:
                enriched.append(
                    {"role": "system", "content": f"{m['content']}\n\n{tool_section}"}
                )
                injected = True
            else:
                enriched.append(m)
        if not injected and tool_section:
            enriched.insert(0, {"role": "system", "content": tool_section})

        try:
            response = self._client.chat_completion(
                messages=enriched,
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        text = response.choices[0].message.content or ""
        tool_calls = self._try_parse_tool_calls(text)
        if tool_calls:
            return LLMResponse(
                content=text,
                tool_calls=tool_calls,
                model=self.model,
                finish_reason=FinishReason.TOOL_CALLS,
                raw=response,
            )
        return LLMResponse(content=text, model=self.model, raw=response)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream the response token-by-token.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters (max_output_tokens, temperature).

        Yields:
            str: Response tokens as they are generated.

        Raises:
            LLMError: If the streaming request fails.
        """
        try:
            for chunk in self._client.chat_completion(
                messages=self._chat_messages(prompt),
                model=self.model,
                max_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                stream=True,
            ):
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    yield delta
        except Exception as exc:
            raise LLMError(f"HuggingFace streaming error: {exc}", cause=exc) from exc

    @staticmethod
    def _try_parse_tool_calls(text: str) -> List[ToolCall]:
        """Attempt to extract tool_calls JSON from model output.

        Used for prompt-based tool calling fallback. Extracts JSON blocks
        containing tool calls from the model's text response.

        Args:
            text: The model's text output to parse.

        Returns:
            List of ToolCall objects extracted from the text, or empty list if parsing fails.
        """
        try:
            # Find JSON block in output
            start = text.find("{")
            end = text.rfind("}") + 1
            if start < 0 or end <= start:
                return []
            data = json.loads(text[start:end])
            calls = data.get("tool_calls", [])
            return [
                ToolCall(tool_name=c["tool_name"], arguments=c.get("arguments", {}))
                for c in calls
                if isinstance(c, dict) and "tool_name" in c
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []
