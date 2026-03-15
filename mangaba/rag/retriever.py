"""
Retriever: wraps an embedding + vector store to find relevant documents.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from mangaba.rag.document import Document
from mangaba.embeddings.base import BaseEmbedding
from mangaba.vectorstores.base import BaseVectorStore


class Retriever:
    """Encapsulates embedding + vector store for similarity search.

    Example::

        retriever = Retriever(embedding=OpenAIEmbedding(key), store=InMemoryVectorStore())
        retriever.add_documents(docs)
        results = retriever.search("What is AI?")
    """

    def __init__(self, embedding: BaseEmbedding, store: BaseVectorStore) -> None:
        self.embedding = embedding
        self.store = store

    def add_documents(self, documents: List[Document]) -> List[str]:
        texts = [d.content for d in documents]
        embeddings = self.embedding.embed_batch(texts)
        metadatas = [d.metadata for d in documents]
        return self.store.add(texts, embeddings, metadatas)

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        query_emb = self.embedding.embed_text(query)
        results = self.store.search(query_emb, top_k=top_k)
        return [
            Document(content=r["content"], metadata={**r.get("metadata", {}), "score": r.get("score", 0)})
            for r in results
        ]

    def clear(self) -> None:
        self.store.clear()
