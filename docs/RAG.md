# 📚 RAG (Retrieval-Augmented Generation)

Pipeline completo para RAG: carregar documentos, splitter, embedding, vector store e chain de Q&A.

---

## Visão Geral

```
Document → Loader → Splitter → Embedding → VectorStore
                                                    ↓
Query → Embedding → Retriever → Top-K Documents → RAGChain → Answer
```

---

## Document

Modelo base para documentos:

```python
from mangaba.rag import Document

doc = Document(
    content="This is the document text content",
    metadata={"source": "file.pdf", "page": 1},
)
```

### Propriedades

| Propriedade | Tipo | Descrição |
|---|---|---|
| `content` | `str` | Conteúdo do documento |
| `metadata` | `dict` | Metadados (fonte, página, etc.) |

---

## Loaders

### TextLoader

```python
from mangaba.rag import TextLoader

loader = TextLoader("path/to/document.txt")
documents = loader.load()
# [Document(content="...", metadata={"source": "document.txt"})]
```

### CSVLoader

```python
from mangaba.rag import CSVLoader

loader = CSVLoader("data.csv", text_columns=["description", "notes"])
documents = loader.load()
# Cada row vira um Document
```

### WebPageLoader

```python
from mangaba.rag.loaders import WebPageLoader

loader = WebPageLoader()
documents = loader.load_urls(["https://example.com/article"])
```

---

## Splitters

### RecursiveTextSplitter

```python
from mangaba.rag import RecursiveTextSplitter

splitter = RecursiveTextSplitter(
    chunk_size=500,     # Tokens por chunk
    chunk_overlap=50,   # Overlap entre chunks
)

# Split texto
chunks = splitter.split_text("Long document text here...")

# Split documents
documents = loader.load()
split_docs = splitter.split_documents(documents)
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `chunk_size` | `int` | `500` | Tamanho do chunk em tokens |
| `chunk_overlap` | `int` | `50` | Overlap entre chunks |

---

## Embeddings

### OpenAIEmbedding

```python
from mangaba.embeddings import OpenAIEmbedding

embed = OpenAIEmbedding(api_key="OPENAI_API_KEY")

# Texto único
vector = embed.embed_text("Hello world")
# [0.012, -0.034, ...]  # 1536 dimensions

# Batch
vectors = embed.embed_batch(["Hello", "World"])
# [[...], [...]]
```

### GoogleEmbedding

```python
from mangaba.embeddings import GoogleEmbedding

embed = GoogleEmbedding(api_key="GOOGLE_API_KEY")
vector = embed.embed_text("Hello world")
# 768 dimensions (text-embedding-004)
```

### HuggingFaceEmbedding

```python
from mangaba.embeddings import HuggingFaceEmbedding

# Local (requires: pip install mangaba[embeddings] or sentence-transformers)
embed = HuggingFaceEmbedding(
    model="sentence-transformers/all-MiniLM-L6-v2",
    use_local=True
)
vector = embed.embed_text("Hello world")
# 384 dimensions, fast and lightweight

# Or using HuggingFace Inference API
embed = HuggingFaceEmbedding(
    model="BAAI/bge-m3",
    api_key="HF_TOKEN",
    use_local=False
)
vector = embed.embed_text("Hello world")
# 1024 dimensions, multilingual

# Batch processing with automatic caching
vectors = embed.embed_batch(["Hello", "World", "Hello"])  # "Hello" cached
```

**Available models:**
- `sentence-transformers/all-MiniLM-L6-v2` - 384d, fast, lightweight
- `BAAI/bge-m3` - 1024d, multilingual, multi-granularity
- `intfloat/multilingual-e5-large-instruct` - 1024d, 100+ languages

---

## Retriever

Bridge entre embeddings e vector store:

```python
from mangaba.rag import Retriever
from mangaba.rag import Document
from mangaba.embeddings import OpenAIEmbedding
from mangaba.vectorstores import InMemoryVectorStore

retriever = Retriever(
    embedding=OpenAIEmbedding(api_key="KEY"),
    store=InMemoryVectorStore(),
)

# Adicionar documentos
docs = [
    Document(content="Python is a programming language", metadata={"topic": "programming"}),
    Document(content="Machine learning uses data to learn patterns", metadata={"topic": "ml"}),
]
retriever.add_documents(docs)

# Buscar
results = retriever.search("What is Python?", top_k=2)
for doc in results:
    print(f"{doc.content} (score: {doc.metadata['score']:.3f})")

# Limpar
retriever.clear()
```

---

## RAGChain

Pipeline completo de Q&A com contexto:

```python
from mangaba.rag import RAGChain
from mangaba.rag import Retriever
from mangaba.core.llm import create_llm_client

# Setup
llm = create_llm_client(provider="google", api_key="KEY", model="gemini-2.5-flash")
retriever = Retriever(
    embedding=OpenAIEmbedding(api_key="KEY"),
    store=InMemoryVectorStore(),
)

# Adicionar documentos ao retriever
retriever.add_documents(documents)

# Criar chain
chain = RAGChain(
    llm=llm,
    retriever=retriever,
    top_k=3,  # Documentos para incluir no contexto
)

# Fazer pergunta
answer = chain.ask("What is machine learning?")
print(answer)
# "Machine learning is a subset of AI that..."
```

---

## Pipeline Completo

```python
from mangaba.rag import (
    Document,
    TextLoader,
    RecursiveTextSplitter,
    Retriever,
    RAGChain,
)
from mangaba.embeddings import OpenAIEmbedding
from mangaba.vectorstores import InMemoryVectorStore
from mangaba.core.llm import create_llm_client

# 1. Carregar documentos
loader = TextLoader("data/knowledge_base.txt")
documents = loader.load()

# 2. Split
splitter = RecursiveTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# 3. Setup embedding + vector store
embedding = OpenAIEmbedding(api_key="KEY")
store = InMemoryVectorStore()

# 4. Retriever
retriever = Retriever(embedding=embedding, store=store)
retriever.add_documents(chunks)

# 5. RAG Chain
llm = create_llm_client(provider="google", api_key="KEY", model="gemini-2.5-flash")
chain = RAGChain(llm=llm, retriever=retriever, top_k=3)

# 6. Perguntar
answer = chain.ask("How do I configure the system?")
print(answer)
```
