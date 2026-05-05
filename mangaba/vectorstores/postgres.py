import json
import psycopg2
import uuid
from psycopg2.extras import execute_values
from typing import List, Dict, Any, Optional
from mangaba.vectorstores import BaseVectorStore


# TODO colocar a lib psycopg2 nos requisitos do projeto (teste e req)
class PostgresVectorStore(BaseVectorStore):

    def __init__(self, connection_string: str, table_name: str = "mangaba_embeddings") -> None:

        self.conn = psycopg2.connect(connection_string)
        self.table = table_name

    def add(
        self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> List[str]:
        ids = [uuid.uuid4().hex[:12] for _ in texts]
        metas = metadatas if metadatas else [{}] * len(texts)
        data = [(ids[i], texts[i], embeddings[i], json.dumps(metas[i])) for i in range(len(texts))]

        with self.conn.cursor() as cur:
            query = f"INSERT INTO {self.table} (id, content, embedding, metadata) VALUES %s"
            execute_values(cur, query, data)
            self.conn.commit()
        return ids

    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT id, content, metadata, (embedding <=> %s::vector) as distance
                FROM {self.table} ORDER BY distance ASC LIMIT %s
            """,
                (query_embedding, top_k),
            )

            return [{"id": r[0], "content": r[1], "score": 1 - r[3], "metadata": r[2]} for r in cur.fetchall()]

    def delete(self, ids: List[str]) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.table} WHERE id = ANY(%s)", (ids,))
            self.conn.commit()

    def clear(self) -> None:
        with self.conn.cursor() as cur:
            cur.execute(f"TRUNCATE TABLE {self.table}")
            self.conn.commit()

    @property
    def count(self) -> int:
        with self.conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self.table}")
            return cur.fetchone()[0]
