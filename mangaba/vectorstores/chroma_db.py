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
    def __init__(self, path: str = "./chroma_db", collection_name: str = "mangaba_collection"):
        if not CHROMA_AVAILABLE:
            raise ImportError(
                "chromadb package is required. Install with: pip install mangaba[chroma]"
            )
        self.client = chromadb.PersistentClient(path=path)
        self.collection = self.client.get_or_create_collection(name=collection_name)

    def add(
        self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        ids = [uuid.uuid4().hex for _ in texts]
        self.collection.add(ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas)
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        results = self.collection.query(query_embeddings=[query_embedding], n_results=top_k)

        final = []
        for i in range(len(results["ids"][0])):
            final.append(
                {
                    "id": results["ids"][0][i],
                    "content": results["documents"][0][i],
                    "score": 1 - results["distances"][0][i],  # Chroma usa distância L2 por padrão, score varia
                    "metadata": results["metadatas"][0][i],
                }
            )
        return final

    def delete(self, ids: List[str]) -> None:
        self.collection.delete(ids=ids)

    def clear(self) -> None:
        all_ids = self.collection.get()["ids"]
        if all_ids:
            self.collection.delete(ids=all_ids)

    @property
    def count(self) -> int:
        return self.collection.count()
