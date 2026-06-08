"""
Redis vector store using RediSearch with HNSW index for vector similarity search.

Requires Redis Stack server with RediSearch and RedisJSON modules enabled.
Install with: pip install mangaba[redis]
"""

from __future__ import annotations

import json
import os
import struct
import time
import uuid
from typing import Any, Dict, List, Optional

from mangaba.vectorstores.base import BaseVectorStore

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    redis = None  # type: ignore[assignment]
    REDIS_AVAILABLE = False


def _get_search_classes():
    """Lazy import RediSearch classes to support mocking in tests.

    Returns:
        A tuple of RediSearch classes.
    """
    from redis.commands.search.field import TextField, VectorField, TagField
    from redis.commands.search.index_definition import IndexDefinition, IndexType
    from redis.commands.search.query import Query
    from redis.commands.json.path import Path

    return TextField, VectorField, TagField, IndexDefinition, IndexType, Query, Path


class RedisVectorStore(BaseVectorStore):
    """Vector store backed by Redis Stack with RediSearch HNSW index.

    This implementation uses Redis Stack's RediSearch module with HNSW indexes
    for efficient vector similarity search.

    Attributes:
        _index_name: The name of the RediSearch index.
        _vector_dimensions: The dimensionality of the vectors.
        _distance_metric: The distance metric to use (COSINE, L2, or IP).
        _key_prefix: The prefix for Redis keys.
        _client: The Redis client connection.
    """

    def __init__(
        self,
        url: str | None = None,
        index_name: str = "mangaba_vectors",
        vector_dimensions: int | None = None,
        embedding_dimensions: int | None = None,
        distance_metric: str = "COSINE",
        hnsw_m: int = 16,
        hnsw_ef_construction: int = 200,
        host: str | None = None,
        port: int | None = None,
        db: int | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the RedisVectorStore.

        Args:
            url: Redis connection URL. If not provided, will try to build from
                host/port/db or read from MANGABA_REDIS_URL/REDIS_URL env vars.
            index_name: The name of the RediSearch index (default: "mangaba_vectors").
            vector_dimensions: The dimensionality of the vectors (deprecated, use
                embedding_dimensions). Default: 1536.
            embedding_dimensions: The dimensionality of the vectors. Default: 1536.
            distance_metric: The distance metric to use (default: "COSINE").
            hnsw_m: The HNSW M parameter (default: 16).
            hnsw_ef_construction: The HNSW EF_CONSTRUCTION parameter (default: 200).
            host: Redis host (if url not provided). Default: localhost.
            port: Redis port (if url not provided). Default: 6379.
            db: Redis database number (if url not provided). Default: 0.
            **kwargs: Additional arguments passed to redis.Redis.from_url.

        Raises:
            ImportError: If redis package is not installed.
            redis.ConnectionError: If connection to Redis fails.
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "redis package is required. Install with: pip install mangaba[redis]"
            )

        # Support both vector_dimensions and embedding_dimensions parameter names
        dimensions = vector_dimensions or embedding_dimensions or 1536

        # Build URL from host/port/db if provided, otherwise use url parameter or default
        if url is None:
            if host or port or db is not None:
                host = host or "localhost"
                port = port or 6379
                db = db if db is not None else 0
                resolved_url = f"redis://{host}:{port}/{db}"
            else:
                resolved_url = (
                    os.getenv("MANGABA_REDIS_URL")
                    or os.getenv("REDIS_URL")
                    or "redis://localhost:6379"
                )
        else:
            resolved_url = url

        self._index_name = index_name
        self._vector_dimensions = dimensions
        self._distance_metric = distance_metric.upper()
        self._key_prefix = f"mangaba:{index_name}:"

        # Connect with retry logic to handle Redis startup delays
        self._client: redis.Redis = self._connect_with_retry(resolved_url, **kwargs)

        self._create_index(
            index_name=index_name,
            vector_dimensions=self._vector_dimensions,
            distance_metric=self._distance_metric,
            hnsw_m=hnsw_m,
            hnsw_ef_construction=hnsw_ef_construction,
        )

    def _connect_with_retry(
        self,
        url: str,
        max_retries: int = 15,
        retry_delay: float = 2.0,
        **kwargs: Any,
    ) -> redis.Redis:
        """Connect to Redis with automatic retry on connection failures.

        Args:
            url: The Redis connection URL.
            max_retries: Maximum number of connection attempts (default: 15).
            retry_delay: Delay between retries in seconds (default: 2.0).
            **kwargs: Additional arguments passed to redis.Redis.from_url.

        Returns:
            A connected Redis client.

        Raises:
            redis.ConnectionError: If connection fails after all retries.
        """
        import sys

        last_error = None
        for attempt in range(max_retries):
            try:
                print(
                    f"[Redis] Attempt {attempt + 1}/{max_retries} to connect to {url.split('@')[-1]}",
                    file=sys.stderr,
                )
                client: redis.Redis = redis.Redis.from_url(
                    url, decode_responses=True, **kwargs
                )
                client.ping()
                print(
                    f"[Redis] ✓ Connected successfully on attempt {attempt + 1}!",
                    file=sys.stderr,
                )
                return client
            except (redis.ConnectionError, ConnectionRefusedError, OSError) as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(
                        f"[Redis] ✗ Connection failed: {e}. Retrying in {retry_delay}s...",
                        file=sys.stderr,
                    )
                    time.sleep(retry_delay)
                    continue

        error_msg = f"Failed to connect to Redis after {max_retries} attempts (waited {max_retries * retry_delay}s total)"
        print(f"[Redis] ✗ {error_msg}", file=sys.stderr)
        raise last_error or redis.ConnectionError(error_msg)

    def _create_index(
        self,
        index_name: str,
        vector_dimensions: int,
        distance_metric: str,
        hnsw_m: int,
        hnsw_ef_construction: int,
    ) -> None:
        """Create the RediSearch index if it doesn't exist.

        Args:
            index_name: The name of the index.
            vector_dimensions: The dimensionality of the vectors.
            distance_metric: The distance metric to use.
            hnsw_m: The HNSW M parameter.
            hnsw_ef_construction: The HNSW EF_CONSTRUCTION parameter.
        """
        TextField, VectorField, TagField, IndexDefinition, IndexType, Query, Path = (
            _get_search_classes()
        )

        try:
            self._client.ft(index_name).info()
            return
        except Exception:
            pass

        schema = (
            TagField("$.id", as_name="id"),
            TextField("$.text", as_name="text", weight=1.0),
            VectorField(
                "$.embedding",
                "HNSW",
                {
                    "TYPE": "FLOAT32",
                    "DIM": vector_dimensions,
                    "DISTANCE_METRIC": distance_metric,
                    "M": hnsw_m,
                    "EF_CONSTRUCTION": hnsw_ef_construction,
                },
                as_name="embedding",
            ),
            TextField("$.metadata", as_name="metadata"),
        )
        definition = IndexDefinition(
            prefix=[self._key_prefix], index_type=IndexType.JSON
        )
        self._client.ft(index_name).create_index(fields=schema, definition=definition)

    def _pack_vector(self, embedding: List[float]) -> bytes:
        """Pack a list of floats into bytes for Redis.

        Args:
            embedding: The embedding vector to pack.

        Returns:
            The packed bytes representation of the vector.
        """
        return struct.pack(f"{len(embedding)}f", *embedding)

    def add(
        self,
        texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> List[str]:
        """Store texts with their embeddings in Redis.

        Args:
            texts: A list of text strings to store.
            embeddings: A list of embedding vectors corresponding to the texts.
            metadatas: Optional list of metadata dictionaries for each text.

        Returns:
            A list of IDs for the stored entries.
        """
        ids: List[str] = []
        pipe = self._client.pipeline(transaction=False)

        for i, (text, emb) in enumerate(zip(texts, embeddings)):
            eid = uuid.uuid4().hex[:12]
            metadata = metadatas[i] if metadatas and i < len(metadatas) else {}

            key = f"{self._key_prefix}{eid}"
            doc = {
                "id": eid,
                "text": text,
                "embedding": [float(x) for x in emb],
                "metadata": json.dumps(metadata),
            }
            pipe.json().set(key, "$", doc)
            ids.append(eid)

        pipe.execute()
        return ids

    def search(
        self, query_embedding: List[float], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Search for similar entries using vector similarity.

        Args:
            query_embedding: The query embedding vector.
            top_k: The maximum number of results to return (default: 5).

        Returns:
            A list of dictionaries containing id, content, score, and metadata
            for each result, sorted by similarity score.
        """
        _, _, _, _, _, Query, _ = _get_search_classes()

        query_vector = self._pack_vector(query_embedding)

        base_query = "*=>[KNN $k @embedding $vector AS score]"
        q = (
            Query(base_query)
            .sort_by("score")
            .return_fields("id", "text", "metadata", "score")
            .dialect(2)
            .paging(0, top_k)
        )

        params = {"k": str(top_k), "vector": query_vector}
        results = self._client.ft(self._index_name).search(q, params)

        output = []
        for doc in results.docs:
            raw_score = (
                float(doc.score)
                if hasattr(doc, "score") and doc.score is not None
                else 0.0
            )

            if self._distance_metric == "COSINE":
                similarity = 1.0 - (raw_score / 2.0)
            elif self._distance_metric == "L2":
                similarity = 1.0 / (1.0 + raw_score) if raw_score > 0 else 1.0
            else:
                similarity = 1.0 - raw_score

            metadata = {}
            if hasattr(doc, "metadata") and doc.metadata:
                try:
                    metadata = json.loads(doc.metadata)
                except (json.JSONDecodeError, TypeError):
                    metadata = {}

            output.append(
                {
                    "id": doc.id if hasattr(doc, "id") else "",
                    "content": doc.text if hasattr(doc, "text") else "",
                    "score": similarity,
                    "metadata": metadata,
                }
            )

        return output

    def delete(self, ids: List[str]) -> None:
        """Delete entries by ID.

        Args:
            ids: A list of IDs to delete.
        """
        pipe = self._client.pipeline(transaction=False)
        for eid in ids:
            key = f"{self._key_prefix}{eid}"
            pipe.delete(key)
        pipe.execute()

    def clear(self) -> None:
        """Remove all entries from the store."""
        cursor = 0
        while True:
            cursor, keys = self._client.scan(
                cursor, match=f"{self._key_prefix}*", count=100
            )
            if keys:
                self._client.delete(*keys)
            if cursor == 0:
                break

    @property
    def count(self) -> int:
        """Return the number of stored entries.

        Returns:
            The number of entries in the store.
        """
        cursor = 0
        total = 0
        while True:
            cursor, keys = self._client.scan(
                cursor, match=f"{self._key_prefix}*", count=100
            )
            total += len(keys)
            if cursor == 0:
                break
        return total

    def close(self) -> None:
        """Close the Redis connection."""
        self._client.close()

    def __del__(self) -> None:
        """Cleanup when the object is deleted."""
        try:
            self.close()
        except Exception:
            pass
