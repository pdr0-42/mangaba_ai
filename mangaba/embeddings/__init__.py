"""Embedding providers for Mangaba AI v3.0"""

from mangaba.embeddings.base import BaseEmbedding
from mangaba.embeddings.openai_embed import OpenAIEmbedding
from mangaba.embeddings.google_embed import GoogleEmbedding

__all__ = ["BaseEmbedding", "OpenAIEmbedding", "GoogleEmbedding"]
