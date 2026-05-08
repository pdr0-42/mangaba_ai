# 🧠 Memory

Sistemas de memória para agents reterem informações entre tasks e conversas.

---

## BaseMemory

Interface abstrata para todos os tipos de memória:

```python
from mangaba.memory import BaseMemory

class BaseMemory:
    def add(self, content: str, metadata: dict = None) -> str: ...
    def search(self, query: str, top_k: int = 5) -> List[dict]: ...
    def get_all(self) -> List[dict]: ...
    def clear(self) -> None: ...
    def get_relevant(self, query: str, max_results: int = 5) -> str: ...
```

---

## ShortTermMemory

Memória volátil com janela deslizante (sliding window):

```python
from mangaba.memory import ShortTermMemory

memory = ShortTermMemory(max_items=50)

# Adicionar memória
memory.add("The user prefers Python over JavaScript", metadata={"type": "preference"})
memory.add("Project deadline is next Friday", metadata={"type": "deadline"})

# Buscar memórias relevantes
results = memory.search("user preferences", top_k=3)
# Retorna as memórias mais relevantes por keyword matching

# Todas as memórias
all_memories = memory.get_all()

# String formatada para injetar no prompt
context = memory.get_relevant("What does the user prefer?")
# "- The user prefers Python over JavaScript"

print(f"Size: {memory.size}")  # 2
memory.clear()
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `max_items` | `int` | `50` | Máximo de itens (oldest são removidos) |

### Características

- ✅ Rápido (deque em memória)
- ✅ Sem dependências externas
- ❌ Volátil (perde ao reiniciar)
- ❌ Busca por keyword simples (sem embeddings)

---

## LongTermMemory

Memória persistente com SQLite e busca vetorial opcional:

```python
from mangaba.memory import LongTermMemory

# Com SQLite apenas
memory = LongTermMemory(db_path="./memory.db")

# Com busca vetorial (requer embedding)
from mangaba.embeddings import OpenAIEmbedding
memory = LongTermMemory(
    db_path="./memory.db",
    embedding=OpenAIEmbedding(api_key="KEY"),
    enable_vector_search=True,
)

# Uso
memory.add("User likes functional programming", metadata={"category": "preference"})
results = memory.search("programming style", top_k=3)
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `db_path` | `str` | `"mangaba_memory.db"` | Path do SQLite |
| `embedding` | `BaseEmbedding` | `None` | Provider de embeddings |
| `enable_vector_search` | `bool` | `False` | Usar busca vetorial |

### Características

- ✅ Persistente (SQLite)
- ✅ Busca vetorial opcional
- ✅ Suporte a metadata
- ❌ Mais lento que ShortTermMemory

---

## EntityMemory

Memória focada em entidades (pessoas, lugares, conceitos):

```python
from mangaba.memory import EntityMemory

memory = EntityMemory()

# Adicionar informações sobre entidades
memory.add("John is the CEO of TechCorp, based in São Paulo")
memory.add("TechCorp raised $10M in Series A funding")

# Buscar por entidade
results = memory.search("John", top_k=3)
# Retorna informações sobre John e entidades relacionadas

# Listar entidades conhecidas
entities = memory.get_entities()
# ["John", "TechCorp", "São Paulo"]
```

### Características

- ✅ Extrai entidades automaticamente
- ✅ Relações entre entidades
- ✅ Busca contextual por entidade

---

## Uso com Agents

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig, MemoryConfig
from mangaba.core.llm import create_llm_client
from mangaba.memory import ShortTermMemory

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# Opção 1: Memory direto
agent = Agent(
    role="Assistant",
    goal="Help the user",
    backstory="Helpful assistant",
    memory=ShortTermMemory(max_items=100),
    llm=llm,
)

# Opção 2: MemoryConfig (cria ShortTermMemory automaticamente)
agent = Agent(
    role="Assistant",
    goal="Help the user",
    backstory="Helpful assistant",
    memory_config=MemoryConfig(
        short_term=True,
        max_short_term_items=100,
    ),
    llm=llm,
)
```

A memória é automaticamente consultada antes de cada task:

```python
# O agent automaticamente:
# 1. Busca memórias relevantes para a task
# 2. Injeta no prompt como contexto
# 3. Salva o resultado na memória após execução
result = agent.execute_task("What did we discuss earlier?")
```
