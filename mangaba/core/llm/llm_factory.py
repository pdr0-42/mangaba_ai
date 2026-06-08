"""
LLM Factory Module

This module provides a factory function to create LLM clients for different providers.
"""

from __future__ import annotations

from typing import Any, Tuple

from .providers.constants import get_providers_dict
from .client import LLMClient


def create_llm_client(
    provider: str, api_key: str, model: str, **options: Any
) -> "LLMClient":
    """Create a unified LLM client for the specified provider.

    Supported providers:
        - "google" / "gemini": Google Gemini models
        - "openai": OpenAI GPT models
        - "anthropic": Anthropic Claude models
        - "huggingface" / "hf": HuggingFace Inference API models
        - "openrouter" / "or" / "open-router": OpenRouter models

    Args:
        provider: Provider name (see supported providers above).
        api_key: API key for the provider.
        model: Model name/ID (e.g., "gpt-4o", "anthropic/claude-3-haiku").
        **options: Provider-specific options (e.g., base_url, temperature, max_tokens).

    For OpenRouter:
        - Use model format like "openai/gpt-4o" or "anthropic/claude-3-haiku"
        - Optional: base_url (default: https://openrouter.ai/api/v1)
        - Optional: site_url, site_name for OpenRouter headers

    Returns:
        LLMClient instance with generate/generate_with_tools methods.

    Raises:
        ValueError: If provider, api_key, or model is not provided.
    """
    from .client import LLMClient

    if not provider:
        raise ValueError("LLM provider name is required")
    if not api_key:
        raise ValueError("API key is required to initialise LLM provider")
    if not model:
        raise ValueError("Model name is required")

    return LLMClient(provider=provider, api_key=api_key, model=model, **options)


def get_supported_providers() -> Tuple[str, ...]:
    """Get all supported provider names and aliases.

    Returns:
        Tuple of all supported provider names and their aliases, sorted alphabetically.
    """
    aliases: set[str] = set()
    PROVIDERS = get_providers_dict()
    for provider_cls in PROVIDERS.values():
        aliases.add(provider_cls.name)
        aliases.update(provider_cls.aliases)
    return tuple(sorted(aliases))
