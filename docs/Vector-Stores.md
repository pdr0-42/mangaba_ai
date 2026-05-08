# 🗄️ Vector Stores

Armazenamento e busca de vetores de embeddings com suporte a 3 backends.

---

## Interface Base

Todos os vector stores implementam `BaseVectorStore`:

```python
from mangaba.vectorstores import BaseVectorStore

class BaseVectorStore:
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: List[dict] = None) -> List[str]: ...
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[dict]: ...
    def delete(self, ids: List[str]) -> None: ...
    def clear(self) -> None: ...
    @property
    def count(self) -> int: ...
```

### Return de `search`

```python
results = store.search(query_embedding, top_k=3)
# [
#     {"id": "abc123", "content": "...", "score": 0.95, "metadata": {...}},
#     {"id": "def456", "content": "...", "score": 0.87, "metadata": {...}},
# ]
```

---

## Factory

```python
from mangaba.vectorstores import create_vectorstore, get_supported_stores

# Ver stores disponíveis
print(get_supported_stores())  # ('inmemory', 'postgres', 'redis')

# Criar store
store = create_vectorstore("inmemory")
store = create_vectorstore("redis", url="redis://localhost:6379", vector_dimensions=1536)
store = create_vectorstore("postgres", url="postgresql://...", vector_dimensions=1536)
```

---

## InMemoryVectorStore

Implementação pura em Python, sem dependências externas:

```python
from mangaba.vectorstores import InMemoryVectorStore

store = InMemoryVectorStore()

# Adicionar
ids = store.add(
    texts=["Python is great", "JavaScript is popular"],
    embeddings=[[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]],
    metadatas=[{"lang": "python"}, {"lang": "js"}],
)

# Buscar (cosine similarity)
results = store.search([0.15, 0.25, 0.35], top_k=1)
print(results[0]["content"])  # "Python is great"

# Deletar
store.delete(ids[:1])

# Contar
print(store.count)  # 1

# Limpar
store.clear()
```

### Características

| Feature | Status |
|---|---|
| Dependências | Nenhuma |
| Persistência | ❌ Volátil |
| Similaridade | Cosine (manual) |
| Escala | Pequena (<10K vetores) |

---

## RedisVectorStore

Redis Stack com RediSearch e índice HNSW para busca vetorial rápida:

### Instalação

```bash
pip install mangaba[redis]
```

### Docker

```bash
docker run -d --name mangaba-redis -p 6379:6379 redis/redis-stack:latest
```

### Uso

```python
from mangaba.vectorstores import RedisVectorStore

store = RedisVectorStore(
    url="redis://localhost:6379",           # Ou env: MANGABA_REDIS_URL
    index_name="my_documents",              # Nome do índice
    vector_dimensions=1536,                 # Dimensões do embedding
    distance_metric="COSINE",               # COSINE, L2, IP
    hnsw_m=16,                              # HNSW M parameter
    hnsw_ef_construction=200,               # HNSW EF construction
)

# Adicionar
ids = store.add(
    texts=["Document 1", "Document 2"],
    embeddings=[[0.1] * 1536, [0.2] * 1536],
    metadatas=[{"source": "file1"}, {"source": "file2"}],
)

# Buscar
results = store.search([0.15] * 1536, top_k=5)

# Deletar, contar, limpar
store.delete(ids[:1])
print(store.count)
store.clear()

# Fechar conexão
store.close()
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `url` | `str` | `redis://localhost:6379` | URL do Redis |
| `index_name` | `str` | `"mangaba_vectors"` | Nome do índice |
| `vector_dimensions` | `int` | `1536` | Dimensões do vetor |
| `distance_metric` | `str` | `"COSINE"` | COSINE, L2, IP |
| `hnsw_m` | `int` | `16` | HNSW M parameter |
| `hnsw_ef_construction` | `int` | `200` | HNSW EF construction |

### Resolução de URL

A URL é resolvida nesta ordem:
1. Parâmetro `url=`
2. Env var `MANGABA_REDIS_URL`
3. Env var `REDIS_URL`
4. Default: `redis://localhost:6379`

### Características

| Feature | Status |
|---|---|
| Dependências | `redis>=5.0.0` |
| Persistência | ✅ Redis AOF/RDB |
| Index | HNSW (RediSearch) |
| Escala | Grande (milhões) |
| Performance | Alta (sub-millisecond) |

---

## PostgresVectorStore

PostgreSQL com extensão pgvector e índice HNSW:

### Instalação

```bash
pip install mangaba[postgres]
```

### Docker

```bash
docker run -d --name mangaba-postgres \
  -e POSTGRES_PASSWORD=minhasenha \
  -p 5432:5432 \
  ankane/pgvector:latest
```

### Uso

```python
from mangaba.vectorstores import PostgresVectorStore

store = PostgresVectorStore(
    url="postgresql://postgres:minhasenha@localhost:5432/mangaba",
    table_name="my_vectors",
    vector_dimensions=1536,
    create_table=True,  # Cria tabela automaticamente
)

# Adicionar
ids = store.add(
    texts=["Document 1", "Document 2"],
    embeddings=[[0.1] * 1536, [0.2] * 1536],
    metadatas=[{"source": "file1"}, {"source": "file2"}],
)

# Buscar
results = store.search([0.15] * 1536, top_k=5)

# Deletar, contar, limpar
store.delete(ids[:1])
print(store.count)
store.clear()

# Fechar conexão
store.close()
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `url` | `str` | *required* | URL de conexão PostgreSQL |
| `table_name` | `str` | `"mangaba_vectors"` | Nome da tabela |
| `vector_dimensions` | `int` | `1536` | Dimensões do vetor |
| `create_table` | `bool` | `True` | Criar tabela automaticamente |

### Resolução de URL

A URL é resolvida nesta ordem:
1. Parâmetro `url=`
2. Env var `MANGABA_VECTORSTORE_URL`
3. Env var `DATABASE_URL`
4. Erro: URL é obrigatória

### Características

| Feature | Status |
|---|---|
| Dependências | `psycopg>=3.1.0` |
| Persistência | ✅ PostgreSQL |
| Index | HNSW (pgvector) |
| Escala | Grande (milhões) |
| ACID | ✅ Transações |

---

## Comparação

| Feature | InMemory | Redis | PostgreSQL |
|---|---|---|---|
| **Persistência** | ❌ | ✅ | ✅ |
| **Performance** | Média | Alta | Alta |
| **Escala** | <10K | Milhões | Milhões |
| **Dependências** | Nenhuma | redis | psycopg |
| **Setup** | Zero | Docker | Docker |
| **Busca** | Cosine manual | HNSW nativo | HNSW nativo |
| **Transações** | ❌ | Pipeline | ✅ ACID |
| **Metadata** | ✅ JSON string | ✅ JSON | ✅ JSONB |

---

## Docker Compose

```yaml
# docker-compose.vectorstores.yml
services:
  redis:
    image: redis/redis-stack:latest
    ports: ["6379:6379", "8001:8001"]

  postgres:
    image: ankane/pgvector:latest
    environment:
      POSTGRES_PASSWORD: minhasenha
    ports: ["5432:5432"]
```

```bash
docker compose -f docker-compose.vectorstores.yml up -d
```
