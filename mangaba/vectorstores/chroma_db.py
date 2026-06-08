"""ChromaDB vector store implementation for Mangaba AI."""

from typing import List, Dict, Any, Optional
import uuid

from mangaba.vectorstores import BaseVectorStore

try:
    import chromadb

    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False


class ChromaVectorStore(BaseVectorStore):
    """Vector store implementation using ChromaDB.

    This implementation uses ChromaDB's persistent client for storing and
    searching vector embeddings.

    Attributes:
        client: The ChromaDB persistent client.
        collection: The ChromaDB collection for storing embeddings.
    """

    def __init__(
        self, path: str = "./chroma_db", collection_name: str = "mangaba_collection"
    ):
        """Initialize the ChromaVectorStore.

        Args:
            path: The path to the ChromaDB database (default: "./chroma_db").
            collection_name: The name of the collection (default: "mangaba_collection").

        Raises:
            ImportError: If chromadb package is not installed.
        """
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb package is required. Install with: pip install mangaba[chroma]"
            )
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Store texts with their embeddings in ChromaDB.

        Args:
            texts: A list of text strings to store.
            embeddings: A list of embedding vectors corresponding to the texts.
            metadatas: Optional list of metadata dictionaries for each text.

        Returns:
            A list of IDs for the stored entries.
        """
        ids = [uuid.uuid4().hex for _ in texts]
        self.collection.add(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar entries in ChromaDB.

        Args:
            query_embedding: The query embedding vector.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of dictionaries containing id, content, score, and metadata
            for each result.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k
        )

        final = []
        for i in range(len(results["ids"][0])):
            final.append(
                {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "score": 1
                    - results["distances"][0][
                        i
                    ],  # Chroma uses L2 distance by default, score varies
                    "metadata": results["metadatas"][0][i],
                }
            )
        return final

    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID.

        Args:
            ids: A list of IDs to delete.
        """
        self.collection.delete(ids=ids)

    def clear(self) -> None:
        """Remove all entries from the collection."""
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)

    @property
    def count(self) -> int:
        """Return the number of stored entries.

        Returns:
            The number of entries in the collection.
        """
        return self.collection.count()
