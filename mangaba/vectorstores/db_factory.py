from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mangaba.vectorstores import BaseVectorStore


class VectorStoreFactory:
    @staticmethod
    def get_store(uri: str, **kwargs) -> BaseVectorStore:
        """
        Instancia o provedor baseado na URI:
        - postgresql://... -> PostgresVectorStore
        - path/to/file.db  -> SQLiteVectorStore
        - chroma://path    -> ChromaVectorStore
        """

        from mangaba.vectorstores import ChromaVectorStore, SQLiteVectorStore, PostgresVectorStore

        if uri.startswith(("postgresql://", "postgres://")):
            return PostgresVectorStore(uri, **kwargs.get("table_name", "mangaba_embeddings"))

        if uri.startswith("chroma://"):
            path = uri.replace("chroma://", "")
            return ChromaVectorStore(path=path, **kwargs)

        if uri.endswith(".db"):
            return SQLiteVectorStore(uri)

        raise ValueError(f"Esquema de conexão não reconhecido para a URI: {uri}")
