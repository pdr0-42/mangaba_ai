from __future__ import annotations

"""
LLM provider engine for Mangaba AI v3.0

Supports native function-calling (tool use), streaming, token counting
and a unified response format across Google, OpenAI, Anthropic and
Hugging Face.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional, Tuple, Type

from mangaba.core.types import (
    FinishReason,
    LLMResponse,
    TokenUsage,
    ToolCall,
)
from mangaba.core.exceptions import (
    AuthenticationError,
    ContentFilterError,
    LLMError,
    RateLimitError,
    RetryableError,
)
from mangaba.core.events import EventBus, Event, EventType

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool schema helpers
# ---------------------------------------------------------------------------

def _tool_to_google_declaration(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Google function declaration format."""
    schema = tool.get_function_schema()
    return {
        "name": schema["name"],
        "description": schema["description"],
        "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
    }


def _tool_to_openai_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to OpenAI function calling format."""
    schema = tool.get_function_schema()
    return {
        "type": "function",
        "function": {
            "name": schema["name"],
            "description": schema["description"],
            "parameters": schema.get("parameters", {"type": "object", "properties": {}}),
        },
    }


def _tool_to_anthropic_schema(tool: Any) -> Dict[str, Any]:
    """Convert a BaseTool to Anthropic tool-use format."""
    schema = tool.get_function_schema()
    return {
        "name": schema["name"],
        "description": schema["description"],
        "input_schema": schema.get("parameters", {"type": "object", "properties": {}}),
    }


def _tools_to_hf_prompt_section(tools: List[Any]) -> str:
    """Render available tools as a system-prompt section for Hugging Face."""
    if not tools:
        return ""
    lines = ["You have access to the following tools:\n"]
    for t in tools:
        schema = t.get_function_schema()
        params = json.dumps(schema.get("parameters", {}), indent=2)
        lines.append(f"### {schema['name']}\n{schema['description']}\nParameters: {params}\n")
    lines.append(
        "To use a tool, respond ONLY with a JSON block:\n"
        '```json\n{"tool_calls": [{"tool_name": "<name>", "arguments": {<args>}}]}\n```\n'
        "If no tool is needed, respond normally."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Base provider
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract interface for LLM providers."""

    name: str = "base"
    aliases: Tuple[str, ...] = ()

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        self.api_key = api_key
        self.model = model
        self.options = options or {}
        self._temperature = options.get("temperature", 0.7)
        self._max_tokens = options.get("max_output_tokens", 1024)
        self._system_prompt = options.get("system_prompt")

    @classmethod
    def matches(cls, provider_name: str) -> bool:
        n = provider_name.lower()
        return n == cls.name or n in cls.aliases

    # -- public API ----------------------------------------------------------

    @abstractmethod
    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        ...

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a response with optional tool/function calling support."""
        # Default: ignore tools and fall back to plain generate
        user_content = ""
        for m in messages:
            if m.get("role") == "user":
                user_content = m.get("content", "")
        return self.generate(user_content, **kwargs)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        """Stream response token-by-token. Default: yield full response."""
        resp = self.generate(prompt, **kwargs)
        yield resp.text

    def count_tokens(self, text: str) -> int:
        """Estimate token count. Default: rough word-based estimate."""
        return max(1, len(text) // 4)


# ---------------------------------------------------------------------------
# Google (Gemini)
# ---------------------------------------------------------------------------

class GoogleLLMProvider(BaseLLMProvider):
    name = "google"
    aliases = ("gemini", "google-ai", "googleai")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
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
        try:
            genai_tools = None
            if tools:
                declarations = [_tool_to_google_declaration(t) for t in tools]
                genai_tools = [self._genai.protos.Tool(function_declarations=[
                    self._genai.protos.FunctionDeclaration(**d) for d in declarations
                ])]

            # Build contents from messages
            contents = []
            for m in messages:
                role = "model" if m["role"] == "assistant" else m["role"]
                if role == "system":
                    continue
                contents.append({"role": role, "parts": [{"text": m.get("content", "")}]})

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
                    tool_calls.append(ToolCall(
                        tool_name=fc.name,
                        arguments=dict(fc.args) if fc.args else {},
                    ))
        except (IndexError, AttributeError):
            text = getattr(response, "text", "") or ""

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(response)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=response)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        try:
            response = self._model.generate_content(prompt, stream=True)
            for chunk in response:
                txt = getattr(chunk, "text", None) or ""
                if txt:
                    yield txt
        except Exception as exc:
            raise LLMError(f"Google streaming error: {exc}", cause=exc) from exc

    def _parse_usage(self, response: Any) -> TokenUsage:
        try:
            um = response.usage_metadata
            return TokenUsage(
                prompt_tokens=getattr(um, "prompt_token_count", 0),
                completion_tokens=getattr(um, "candidates_token_count", 0),
                total_tokens=getattr(um, "total_token_count", 0),
            )
        except Exception:
            return TokenUsage()


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

class OpenAILLMProvider(BaseLLMProvider):
    name = "openai"
    aliases = ("gpt", "chatgpt")

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'openai' not found. Install with: pip install openai") from exc
        self._client = OpenAI(api_key=api_key)

    def _build_messages(self, prompt: str, system_prompt: Optional[str] = None) -> List[Dict[str, str]]:
        msgs: List[Dict[str, str]] = []
        sp = system_prompt or self._system_prompt
        if sp:
            msgs.append({"role": "system", "content": sp})
        msgs.append({"role": "user", "content": prompt})
        return msgs

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
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
                args = json.loads(tc.function.arguments) if tc.function.arguments else {}
                tool_calls.append(ToolCall(id=tc.id, tool_name=tc.function.name, arguments=args))

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=resp)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        msgs = self._build_messages(prompt, kwargs.pop("system_prompt", None))
        try:
            stream = self._client.chat.completions.create(
                model=self.model, messages=msgs,
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
        try:
            import tiktoken  # type: ignore
            enc = tiktoken.encoding_for_model(self.model)
            return len(enc.encode(text))
        except Exception:
            return super().count_tokens(text)

    def _parse_usage(self, resp: Any) -> TokenUsage:
        if resp.usage:
            return TokenUsage(
                prompt_tokens=resp.usage.prompt_tokens or 0,
                completion_tokens=resp.usage.completion_tokens or 0,
                total_tokens=resp.usage.total_tokens or 0,
            )
        return TokenUsage()

    def _handle_openai_error(self, exc: Exception) -> None:
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc


# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------

class AnthropicLLMProvider(BaseLLMProvider):
    name = "anthropic"
    aliases = ("claude",)

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from anthropic import Anthropic  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'anthropic' not found. Install with: pip install anthropic") from exc
        self._client = Anthropic(api_key=api_key)

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
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

        parts = [getattr(b, "text", "") for b in resp.content if getattr(b, "type", "") == "text"]
        text = "\n".join(p for p in parts if p)
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, usage=usage, model=self.model, raw=resp)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        anthropic_tools = [_tool_to_anthropic_schema(t) for t in tools] if tools else None
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
                tool_calls.append(ToolCall(
                    id=block.id,
                    tool_name=block.name,
                    arguments=block.input if isinstance(block.input, dict) else {},
                ))

        finish = FinishReason.TOOL_CALLS if tool_calls else FinishReason.STOP
        usage = self._parse_usage(resp)
        return LLMResponse(content=text, tool_calls=tool_calls, usage=usage, model=self.model, finish_reason=finish, raw=resp)

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
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
        if hasattr(resp, "usage") and resp.usage:
            return TokenUsage(
                prompt_tokens=getattr(resp.usage, "input_tokens", 0),
                completion_tokens=getattr(resp.usage, "output_tokens", 0),
                total_tokens=getattr(resp.usage, "input_tokens", 0) + getattr(resp.usage, "output_tokens", 0),
            )
        return TokenUsage()

    def _handle_anthropic_error(self, exc: Exception) -> None:
        exc_name = type(exc).__name__
        if "AuthenticationError" in exc_name:
            raise AuthenticationError(str(exc), cause=exc) from exc
        if "RateLimitError" in exc_name:
            raise RateLimitError(str(exc), cause=exc) from exc
        if "APITimeoutError" in exc_name or "APIConnectionError" in exc_name:
            raise RetryableError(str(exc), cause=exc) from exc


# ---------------------------------------------------------------------------
# Hugging Face – open-model catalogue
# ---------------------------------------------------------------------------

# Curated list of models available via HuggingFace Inference API.
# Fields: id, name, category, context_window, tool_calling, streaming, notes
HF_OPEN_MODELS: List[Dict[str, Any]] = [
    # ── Instruction-tuned general ──────────────────────────────────────────
    {"id": "mistralai/Mistral-7B-Instruct-v0.3",       "name": "Mistral 7B Instruct v0.3",       "category": "general",    "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "default; fast, strong 7B"},
    {"id": "mistralai/Mixtral-8x7B-Instruct-v0.1",     "name": "Mixtral 8x7B Instruct",          "category": "general",    "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "MoE, quality close to GPT-3.5"},
    {"id": "mistralai/Mixtral-8x22B-Instruct-v0.1",    "name": "Mixtral 8x22B Instruct",         "category": "general",    "context": 65536,  "tool_calling": False, "streaming": True,  "notes": "MoE, near GPT-4 quality"},
    {"id": "mistralai/Mistral-Nemo-Instruct-2407",      "name": "Mistral Nemo 12B Instruct",      "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "128k context, multilingual"},
    # ── Meta Llama 3 ──────────────────────────────────────────────────────
    {"id": "meta-llama/Meta-Llama-3-8B-Instruct",      "name": "Llama 3 8B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "fast, lightweight"},
    {"id": "meta-llama/Meta-Llama-3-70B-Instruct",     "name": "Llama 3 70B Instruct",           "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "high quality"},
    {"id": "meta-llama/Meta-Llama-3.1-8B-Instruct",    "name": "Llama 3.1 8B Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "128k context"},
    {"id": "meta-llama/Meta-Llama-3.1-70B-Instruct",   "name": "Llama 3.1 70B Instruct",         "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "128k context, top open model"},
    {"id": "meta-llama/Meta-Llama-3.1-405B-Instruct",  "name": "Llama 3.1 405B Instruct",        "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "largest open model; PRO required"},
    {"id": "meta-llama/Llama-3.2-1B-Instruct",         "name": "Llama 3.2 1B Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "ultra-light edge model"},
    {"id": "meta-llama/Llama-3.2-3B-Instruct",         "name": "Llama 3.2 3B Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "edge-friendly"},
    # ── Code ──────────────────────────────────────────────────────────────
    {"id": "bigcode/starcoder2-15b-instruct-v0.1",     "name": "StarCoder2 15B Instruct",        "category": "code",       "context": 16384,  "tool_calling": False, "streaming": True,  "notes": "code generation & completion"},
    {"id": "Qwen/Qwen2.5-Coder-7B-Instruct",           "name": "Qwen 2.5 Coder 7B Instruct",     "category": "code",       "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "strong coding, multilingual"},
    {"id": "Qwen/Qwen2.5-Coder-32B-Instruct",          "name": "Qwen 2.5 Coder 32B Instruct",    "category": "code",       "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "top open code model"},
    {"id": "deepseek-ai/deepseek-coder-33b-instruct",  "name": "DeepSeek Coder 33B Instruct",    "category": "code",       "context": 16384,  "tool_calling": False, "streaming": True,  "notes": "competitive code assistant"},
    # ── Qwen general ──────────────────────────────────────────────────────
    {"id": "Qwen/Qwen2.5-7B-Instruct",                 "name": "Qwen 2.5 7B Instruct",           "category": "general",    "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "multilingual, strong benchmarks"},
    {"id": "Qwen/Qwen2.5-72B-Instruct",                "name": "Qwen 2.5 72B Instruct",          "category": "general",    "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "near GPT-4 quality open model"},
    # ── Phi (Microsoft) ───────────────────────────────────────────────────
    {"id": "microsoft/Phi-3-mini-4k-instruct",         "name": "Phi-3 Mini 4K Instruct",         "category": "general",    "context": 4096,   "tool_calling": False, "streaming": True,  "notes": "3.8B, efficient small model"},
    {"id": "microsoft/Phi-3-medium-128k-instruct",     "name": "Phi-3 Medium 128K Instruct",     "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "14B, 128k context"},
    {"id": "microsoft/Phi-3.5-mini-instruct",          "name": "Phi-3.5 Mini Instruct",          "category": "general",    "context": 128000, "tool_calling": False, "streaming": True,  "notes": "3.8B, multilingual"},
    # ── Gemma (Google) ────────────────────────────────────────────────────
    {"id": "google/gemma-2-2b-it",                     "name": "Gemma 2 2B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "tiny but capable"},
    {"id": "google/gemma-2-9b-it",                     "name": "Gemma 2 9B Instruct",            "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "strong 9B model"},
    {"id": "google/gemma-2-27b-it",                    "name": "Gemma 2 27B Instruct",           "category": "general",    "context": 8192,   "tool_calling": False, "streaming": True,  "notes": "top Gemma, near 70B quality"},
    # ── Math / Reasoning ──────────────────────────────────────────────────
    {"id": "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",  "name": "DeepSeek R1 Distill Qwen 7B",   "category": "reasoning",  "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "chain-of-thought reasoning"},
    {"id": "deepseek-ai/DeepSeek-R1-Distill-Llama-70B","name": "DeepSeek R1 Distill Llama 70B", "category": "reasoning",  "context": 32768,  "tool_calling": False, "streaming": True,  "notes": "top open reasoning model"},
    # ── Embeddings ────────────────────────────────────────────────────────
    {"id": "BAAI/bge-m3",                              "name": "BGE-M3",                         "category": "embedding",  "context": 8192,   "tool_calling": False, "streaming": False, "notes": "multilingual, multi-granularity"},
    {"id": "sentence-transformers/all-MiniLM-L6-v2",   "name": "all-MiniLM-L6-v2",              "category": "embedding",  "context": 512,    "tool_calling": False, "streaming": False, "notes": "fast, lightweight embeddings"},
    {"id": "intfloat/multilingual-e5-large-instruct",  "name": "Multilingual E5 Large Instruct", "category": "embedding",  "context": 512,    "tool_calling": False, "streaming": False, "notes": "100+ languages"},
]

# Index by category for quick lookup
_HF_MODELS_BY_CATEGORY: Dict[str, List[Dict[str, Any]]] = {}
for _m in HF_OPEN_MODELS:
    _HF_MODELS_BY_CATEGORY.setdefault(_m["category"], []).append(_m)


def list_huggingface_models(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return curated HuggingFace open models, optionally filtered by category.

    Categories: general, code, reasoning, embedding.
    """
    if category:
        return [m for m in HF_OPEN_MODELS if m["category"] == category]
    return list(HF_OPEN_MODELS)


# ---------------------------------------------------------------------------
# Hugging Face – provider
# ---------------------------------------------------------------------------

class HuggingFaceLLMProvider(BaseLLMProvider):
    """Hugging Face Inference API. Uses prompt-engineering for tool use."""

    name = "huggingface"
    aliases = ("hf", "hugging-face")

    SUPPORTED_MODELS: Tuple[str, ...] = tuple(
        m["id"] for m in HF_OPEN_MODELS if m["category"] != "embedding"
    )

    def __init__(self, api_key: str, model: str, **options: Any) -> None:
        super().__init__(api_key, model, **options)
        try:
            from huggingface_hub import InferenceClient  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise ImportError("Package 'huggingface-hub' not found. Install with: pip install huggingface-hub") from exc
        self._client = InferenceClient(token=api_key)

    @classmethod
    def list_models(cls, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return curated open models available via HuggingFace Inference API."""
        return list_huggingface_models(category=category)

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
        try:
            response = self._client.text_generation(
                prompt,
                model=self.model,
                max_new_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                return_full_text=False,
            )
        except Exception as exc:
            raise LLMError(f"HuggingFace error: {exc}", cause=exc) from exc

        text = response if isinstance(response, str) else (response.get("generated_text") or "")
        return LLMResponse(content=text, model=self.model, raw=response)

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        # Build prompt with tool descriptions injected
        tool_section = _tools_to_hf_prompt_section(tools or [])
        parts = []
        for m in messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if role == "system":
                parts.append(f"{content}\n\n{tool_section}")
            else:
                parts.append(f"{role}: {content}")
        if not any(m.get("role") == "system" for m in messages) and tool_section:
            parts.insert(0, tool_section)

        prompt = "\n\n".join(parts)
        resp = self.generate(prompt, **kwargs)

        # Try to parse tool calls from output
        tool_calls = self._try_parse_tool_calls(resp.text)
        if tool_calls:
            return LLMResponse(
                content=resp.text, tool_calls=tool_calls,
                model=self.model, finish_reason=FinishReason.TOOL_CALLS, raw=resp.raw,
            )
        return resp

    def stream(self, prompt: str, **kwargs: Any) -> Iterator[str]:
        try:
            stream = self._client.text_generation(
                prompt, model=self.model,
                max_new_tokens=kwargs.get("max_output_tokens", self._max_tokens),
                temperature=kwargs.get("temperature", self._temperature),
                return_full_text=False, stream=True,
            )
            for token in stream:
                txt = token if isinstance(token, str) else getattr(token, "token", {}).get("text", "")
                if txt:
                    yield txt
        except Exception as exc:
            raise LLMError(f"HuggingFace streaming error: {exc}", cause=exc) from exc

    @staticmethod
    def _try_parse_tool_calls(text: str) -> List[ToolCall]:
        """Attempt to extract tool_calls JSON from model output."""
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
                for c in calls if isinstance(c, dict) and "tool_name" in c
            ]
        except (json.JSONDecodeError, KeyError, TypeError):
            return []


# ---------------------------------------------------------------------------
# Provider registry
# ---------------------------------------------------------------------------

PROVIDERS: Dict[str, Type[BaseLLMProvider]] = {
    GoogleLLMProvider.name: GoogleLLMProvider,
    OpenAILLMProvider.name: OpenAILLMProvider,
    AnthropicLLMProvider.name: AnthropicLLMProvider,
    HuggingFaceLLMProvider.name: HuggingFaceLLMProvider,
}


def _resolve_provider_class(provider_name: str) -> Type[BaseLLMProvider]:
    normalized = provider_name.lower()
    for name, provider_cls in PROVIDERS.items():
        if provider_cls.matches(normalized):
            return provider_cls
    supported = ", ".join(sorted(PROVIDERS.keys()))
    raise ValueError(f"LLM provider '{provider_name}' not supported. Valid options: {supported}")


# ---------------------------------------------------------------------------
# High-level client
# ---------------------------------------------------------------------------

class LLMClient:
    """Unified high-level LLM client with tool use and streaming support."""

    def __init__(self, provider: str, api_key: str, model: str, **options: Any) -> None:
        provider_cls = _resolve_provider_class(provider)
        self.provider_name = provider_cls.name
        self._provider = provider_cls(api_key=api_key, model=model, **options)
        self._usage_tracker: List[TokenUsage] = []

    # -- basic generation ---------------------------------------------------

    def generate(self, prompt: str, **kwargs: Any) -> LLMResponse:
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
        return self.generate(prompt, **kwargs).text

    # -- tool use -----------------------------------------------------------

    def generate_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
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
        return self._provider.stream(prompt, **kwargs)

    # -- token counting -----------------------------------------------------

    def count_tokens(self, text: str) -> int:
        return self._provider.count_tokens(text)

    # -- usage tracking -----------------------------------------------------

    @property
    def total_usage(self) -> TokenUsage:
        total = TokenUsage()
        for u in self._usage_tracker:
            total.prompt_tokens += u.prompt_tokens
            total.completion_tokens += u.completion_tokens
            total.total_tokens += u.total_tokens
        return total

    def _track_usage(self, usage: TokenUsage) -> None:
        if usage.total_tokens > 0:
            self._usage_tracker.append(usage)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

def create_llm_client(provider: str, api_key: str, model: str, **options: Any) -> LLMClient:
    if not provider:
        raise ValueError("LLM provider name is required")
    if not api_key:
        raise ValueError("API key is required to initialise LLM provider")
    if not model:
        raise ValueError("Model name is required")
    return LLMClient(provider=provider, api_key=api_key, model=model, **options)


def get_supported_providers() -> Tuple[str, ...]:
    aliases: set[str] = set()
    for provider_cls in PROVIDERS.values():
        aliases.add(provider_cls.name)
        aliases.update(provider_cls.aliases)
    return tuple(sorted(aliases))
