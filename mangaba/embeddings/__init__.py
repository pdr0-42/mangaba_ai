"""Embedding providers for Mangaba AI v3.0.

This module provides text embedding functionality for semantic search
and RAG applications, with support for multiple providers:

- OpenAIEmbedding: OpenAI's text-embedding models
- GoogleEmbedding: Google's embedding API
- HuggingFaceEmbedding: Open-source models via HuggingFace

All providers implement the BaseEmbedding interface for consistency.
"""

from mangaba.embeddings.base import BaseEmbedding
from mangaba.embeddings.openai_embed import OpenAIEmbedding
from mangaba.embeddings.google_embed import GoogleEmbedding
from mangaba.embeddings.huggingface_embed import HuggingFaceEmbedding

__all__ = [
    "BaseEmbedding",
    "OpenAIEmbedding",
    "GoogleEmbedding",
    "HuggingFaceEmbedding",
]
