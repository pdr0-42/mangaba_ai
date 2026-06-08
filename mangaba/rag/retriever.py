"""
Retriever: wraps an embedding + vector store to find relevant documents.
"""

from __future__ import annotations

from typing import List

from mangaba.rag.document import Document
from mangaba.embeddings.base import BaseEmbedding
from mangaba.vectorstores.base import BaseVectorStore


class Retriever:
    """Encapsulates embedding and vector store for similarity search.

    This class combines an embedding model with a vector store to provide
    document retrieval functionality based on semantic similarity.

    Example::

        retriever = Retriever(embedding=OpenAIEmbedding(key), store=InMemoryVectorStore())
        retriever.add_documents(docs)
        results = retriever.search("What is AI?")

    Attributes:
        embedding: The embedding model to use for text vectorization.
        store: The vector store to use for document storage and search.
    """

    def __init__(self, embedding: BaseEmbedding, store: BaseVectorStore) -> None:
        """Initialize the Retriever.

        Args:
            embedding: The embedding model to use for text vectorization.
            store: The vector store to use for document storage and search.
        """
        self.embedding = embedding
        self.store = store

    def add_documents(self, documents: List[Document]) -> List[str]:
        """Add documents to the vector store.

        Args:
            documents: A list of Document objects to add.

        Returns:
            A list of IDs for the added documents.
        """
        texts = [d.content for d in documents]
        embeddings = self.embedding.embed_batch(texts)
        metadatas = [d.metadata for d in documents]
        return self.store.add(texts, embeddings, metadatas)

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """Search for documents similar to the query.

        Args:
            query: The search query.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of Document objects sorted by similarity score.
        """
        query_emb = self.embedding.embed_text(query)
        results = self.store.search(query_emb, top_k=top_k)
        return [
            Document(
                content=r["content"],
                metadata={**r.get("metadata", {}), "score": r.get("score", 0)},
            )
            for r in results
        ]

    def clear(self) -> None:
        """Clear all documents from the vector store."""
        self.store.clear()
