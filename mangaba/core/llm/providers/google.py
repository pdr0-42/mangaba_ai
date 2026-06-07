"""Google (Gemini) LLM provider."""

from typing import Any, List, Dict, Optional, Iterator
from mangaba.core.llm.base import BaseLLMProvider
from mangaba.core.types import LLMResponse, TokenUsage, FinishReason, ToolCall
from mangaba.core.exceptions import LLMError
from .schemas import _tool_to_google_declaration


class GoogleLLMProvider(BaseLLMProvider):
    name = "google"
    aliases = ("gemini", "google-ai", "googleai")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        """Initialize the Google Gemini LLM provider.

        Args:
            api_key: Google AI API key.
            model: Model name (e.g., "gemini-2.5-flash", "gemini-2.5-pro").
            **options: Additional provider-specific options (generation_config, safety_settings).

        Raises:
            ImportError: If the google-generativeai package is not installed.
        """
        super().__init__(api_key, model, **options)
        try:
            import google.generativeai as genai  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "Package 'google-generativeai' not found. Install with: pip install google-generativeai"
            ) from exc

        genai.configure(api_key=api_key)
        gen_cfg = options.get("generation_config")
        safety = options.get("safety_settings")
        if gen_cfg is None:
            gen_cfg = {
                k: options.get(k)
                for k in ("temperature", "top_p", "top_k", "max_output_tokens")
                if options.get(k) is not None
            } or None

        self._model = genai.GenerativeModel(
            model_name=model,
            generation_config=gen_cfg,
            safety_settings=safety,
        )
        self._genai = genai

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        """Generate a response from Google Gemini.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters to pass to the API.

        Returns:
            LLMResponse containing the generated text, usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        try:
            response = self._model.generate_content(
                prompt, **{k: v for k, v in kwargs.items() if v is not None}
            )
        except Exception as exc:
            raise LLMError(f"Google LLM error: {exc}", cause=exc) from exc

        text = getattr(response, "text", None) or ""
        usage = self._parse_usage(response)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=response)

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
            **kwargs: Additional parameters to pass to the API.

        Returns:
            LLMResponse containing text, tool calls (if any), usage metadata, and raw response.

        Raises:
            LLMError: If the API request fails.
        """
        try:
            genai_tools = None
            if tools:
                declarations = [_tool_to_google_declaration(t) for t in tools]
                genai_tools = [
                    self._genai.protos.Tool(
                        function_declarations=[
                            self._genai.protos.FunctionDeclaration(**d)
                            for d in declarations
                        ]
                    )
                ]

            # Build contents from messages
            contents = []
            for m in messages:
                role = "model" if m["role"] == "assistant" else m["role"]
                if role == "system":
                    continue
                contents.append(
                    {"role": role, "parts": [{"text": m.get("content", "")}]}
                )

            response = self._model.generate_content(
                contents,
                tools=genai_tools,
                **{k: v for k, v in kwargs.items() if v is not None},
            )
        except Exception as exc:
            raise LLMError(f"Google LLM error: {exc}", cause=exc) from exc

        text = ""
        tool_calls: List[ToolCall] = []
        try:
            for part in response.candidates[0].content.parts:
                if hasattr(part, "text") and part.text:
                    text += part.text
                elif hasattr(part, "function_call") and part.function_call:
                    fc = part.function_call
                    tool_calls.append(
                        ToolCall(
                            tool_name=fc.name,
                            arguments=dict(fc.args) if fc.args else {},
                        )
                    )
        except (IndexError, AttributeError):
            text = getattr(response, "text", "") or ""

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(response)
        return LLMResponse(
            content=text,
            tool_calls=tool_calls,
            usage=usage,
            model=self.model,
            finish_reason=finish,
            raw=response,
        )

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream the response token-by-token.

        Args:
            prompt: The input prompt to generate a response for.
            **kwargs: Additional parameters to pass to the API.

        Yields:
            str: Response tokens as they are generated.

        Raises:
            LLMError: If the streaming request fails.
        """
        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                txt = getattr(chunk, "text", None) or ""
                if txt:
                    yield txt
        except Exception as exc:
            raise LLMError(f"Google streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, response: Any) -> TokenUsage:
        """Parse token usage from Google response.

        Args:
            response: The Google API response object.

        Returns:
            TokenUsage object with prompt_tokens, completion_tokens, and total_tokens.
        """
        try:
            um = response.usage_metadata
            return TokenUsage(
                prompt_tokens=getattr(um, "prompt_token_count", 0),
                completion_tokens=getattr(um, "candidates_token_count", 0),
                total_tokens=getattr(um, "total_token_count", 0),
            )
        except Exception:
            return TokenUsage()
