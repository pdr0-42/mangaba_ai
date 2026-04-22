# 🥭 Mangaba AI

[![PyPI version](https://img.shields.io/pypi/v/mangaba.svg)](https://pypi.org/project/mangaba/)
[![Python](https://img.shields.io/pypi/pyversions/mangaba.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/usuario/mangaba-ai/actions)

**Framework profissional de orquestração multi-agente** com ReAct reasoning, function calling nativo, RAG, memória persistente e suporte a 4 provedores LLM.

> Alternativa leve e completa a CrewAI + LangChain em um único pacote.

## ✨ Destaques v3.0

- 🧠 **ReAct Reasoning** — Loop Thought→Action→Observation com function calling nativo
- 🤖 **4 Provedores LLM** — Google Gemini, OpenAI GPT, Anthropic Claude, HuggingFace
- 👥 **4 Processos de Crew** — Sequential, Hierarchical, Parallel (asyncio), Consensual
- 🔧 **Tool System** — `@tool` decorator, Pydantic schemas, JSON schema automático para LLM
- 📚 **RAG Pipeline** — Document loaders, text splitters, embeddings, vector store, retriever
- 💾 **Memória** — Curto prazo (sliding window), longo prazo (SQLite), entidades
- 🛡️ **Guardrails** — Validação de tamanho, filtro de conteúdo, schema validation
- 📊 **Observabilidade** — EventBus com 22+ tipos de evento, callbacks console/arquivo
- 🔄 **Workflow Engine** — Pipelines com stages sequenciais, paralelos e condicionais
- ⚡ **Cache & Retry** — Cache LRU + disco (SQLite), retry com backoff exponencial

## 🚀 Instalação

```bash
pip install mangaba

# Com RAG e embeddings
pip install mangaba[all]

# Desenvolvimento
pip install mangaba[dev]
```

## ⚡ Quick Start

### Agente simples com ferramenta

```python
from mangaba import Agent, Task, Crew, Process, tool

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information",
    backstory="Expert researcher with 10 years of experience",
    tools=[search],
    llm_config={"provider": "google", "api_key": "YOUR_KEY"},
)

task = Task(
    description="Research the latest AI trends in 2026",
    expected_output="A list of the top 5 trends with explanations",
    agent=researcher,
)

crew = Crew(
    agents=[researcher],
    tasks=[task],
    process=Process.SEQUENTIAL,
)

result = crew.kickoff()
print(result.final_output)
```

### Pipeline com stages

```python
from mangaba import Pipeline, Stage, ParallelStage

pipeline = Pipeline(stages=[
    Stage("research", [research_task]),
    ParallelStage("analysis", [task_a, task_b]),
    Stage("report", [write_task]),
])

result = pipeline.run({"topic": "AI"})
```

### RAG (Retrieval-Augmented Generation)

```python
from mangaba.rag import TextLoader, RecursiveTextSplitter, RAGChain, Retriever
from mangaba.embeddings import OpenAIEmbedding
from mangaba.vectorstores import InMemoryVectorStore

# Carregar e dividir documentos
docs = TextLoader("data.txt").load()
chunks = RecursiveTextSplitter(chunk_size=500).split_documents(docs)

# Criar retriever
embedding = OpenAIEmbedding(api_key="YOUR_KEY")
store = InMemoryVectorStore(embedding)
store.add(chunks)
retriever = Retriever(embedding=embedding, vector_store=store)

# RAG chain
from mangaba.core.llm import create_llm_client
llm = create_llm_client(provider="google", api_key="YOUR_KEY")
chain = RAGChain(llm=llm, retriever=retriever)
answer = chain.query("What are the main topics?")
```

### Memória persistente

```python
from mangaba.memory import ShortTermMemory, LongTermMemory

# Curto prazo (últimas N interações)
short = ShortTermMemory(max_items=50)
short.add("User asked about Python")

# Longo prazo (SQLite)
long_mem = LongTermMemory(storage_path="memory.db")
long_mem.add("User prefers concise answers")
results = long_mem.search("preferences")
```

### Guardrails e Output Parsers

```python
from mangaba import Agent, Task
from mangaba.core.guardrails import LengthGuardrail, GuardrailChain
from mangaba.core.output_parsers import JSONOutputParser

task = Task(
    description="List the top 3 programming languages",
    expected_output="JSON with name and reason",
    agent=agent,
    guardrails=[LengthGuardrail(max_length=2000)],
    output_parser=JSONOutputParser(),
)
```

### Observabilidade com EventBus

```python
from mangaba import EventBus
from mangaba.callbacks import ConsoleCallback, FileCallback

# Ativar logging de eventos
EventBus.register(ConsoleCallback())
EventBus.register(FileCallback("events.jsonl"))

# Todos os eventos (agent, task, tool, LLM, crew) são capturados automaticamente
result = crew.kickoff()
```

## 🏛️ Padrões de Projeto

O Mangaba aplica padrões GoF de forma consistente em toda a base de código:

| Padrão | Onde é usado |
|---|---|
| **Factory** | `create_llm_client()` — instancia o provider correto por nome |
| **Abstract Factory** | `BaseLLMProvider` — interface comum; cada provider é uma família concreta |
| **Facade** | `LLMClient` — esconde a complexidade dos 4 providers atrás de uma API uniforme |
| **Decorator** | `@tool` — converte funções Python em `BaseTool` com schema automático |
| **Composite** | `Crew` — agrega múltiplos `Agent` + `Task` e os executa como unidade |
| **Strategy** | `Process` (sequential/hierarchical/parallel/consensual); providers como strategies |
| **Observer** | `EventBus` + callbacks (`ConsoleCallback`, `FileCallback`) |
| **Template Method** | `BaseLLMProvider.generate/stream/generate_with_tools` — subclasses implementam os passos |
| **Chain of Responsibility** | `GuardrailChain` — passa o output por validadores em sequência |
| **Command** | `Task` — encapsula instrução, agente e ferramentas |
| **Iterator** | `stream()` — retorna `Iterator[str]` token a token |
| **Pipes & Filters** | `Pipeline → Stage[] → ParallelStage / ConditionalStage` |

## 🏗️ Arquitetura

```
mangaba/
├── core/               # Cérebro do framework
│   ├── agent.py            # Agent com ReAct reasoning
│   ├── task.py             # Tasks com guardrails e retry
│   ├── crew.py             # Orquestração (4 processos)
│   ├── workflow.py         # Pipeline engine
│   ├── reasoning.py        # ReAct loop (Think→Act→Observe)
│   ├── guardrails.py       # Validação de outputs
│   ├── output_parsers.py   # JSON, Pydantic, List, Markdown
│   ├── planner.py          # Decomposição automática de tarefas
│   ├── types.py            # Tipos Pydantic v2
│   ├── exceptions.py       # Hierarquia de exceções
│   ├── events.py           # EventBus (22+ event types)
│   └── llm/                # Engine LLM multi-provider
│       ├── client.py           # 4 providers + function calling + streaming
│       ├── retry.py            # Retry com backoff exponencial
│       ├── cache.py            # LRU (memória) + SQLite (disco)
│       ├── token_counter.py    # Contagem de tokens
│       └── prompt_templates.py # Templates de prompt
├── tools/              # Sistema de ferramentas
│   ├── base.py             # BaseTool + JSON schema automático
│   ├── decorator.py        # @tool decorator
│   ├── toolkit.py          # Agrupamento de ferramentas
│   ├── file_tools.py       # FileReader, FileWriter, DirectoryList
│   ├── web_search.py       # Serper, DuckDuckGo
│   ├── math_tools.py       # Calculadora segura (AST)
│   └── text_tools.py       # TextSplitter, WordCounter
├── memory/             # Sistema de memória
│   ├── short_term.py       # Sliding window (deque)
│   ├── long_term.py        # SQLite + embeddings opcionais
│   └── entity.py           # Memória de entidades
├── embeddings/         # Provedores de embedding
│   ├── openai_embed.py     # text-embedding-3-small
│   └── google_embed.py     # text-embedding-004
├── vectorstores/       # Armazenamento vetorial
│   └── in_memory.py        # Cosine similarity
├── rag/                # Pipeline RAG
│   ├── document.py         # Modelo de documento
│   ├── loaders.py          # Text, CSV, WebPage
│   ├── splitters.py        # RecursiveTextSplitter
│   ├── retriever.py        # Embedding + vector store
│   └── chain.py            # RAGChain com fontes
└── callbacks/          # Observabilidade
    ├── console.py          # Print formatado de eventos
    └── file.py             # Log JSONL
```

## 🔄 Processos de Crew

| Processo | Descrição | Uso |
|---|---|---|
| `SEQUENTIAL` | Tarefas executadas em ordem, uma após a outra | Workflows lineares |
| `HIERARCHICAL` | Primeiro agente é manager, delega e revisa | Equipes com líder |
| `PARALLEL` | Tarefas executadas concorrentemente (asyncio) | Tarefas independentes |
| `CONSENSUAL` | Todos os agentes executam cada tarefa, resultado sintetizado | Decisões críticas |

## 🌐 Provedores LLM

| Provedor | Function Calling | Streaming | Modelo Padrão |
|---|---|---|---|
| **Google Gemini** | ✅ Nativo | ✅ | `gemini-2.5-flash` |
| **OpenAI** | ✅ Nativo | ✅ | `gpt-4o-mini` |
| **Anthropic** | ✅ Nativo (tool_use) | ✅ | `claude-3-haiku-20240307` |
| **HuggingFace** | ✅ Nativo (11 modelos) / ⚠️ Prompt (14 modelos) | ✅ via `chat_completion` | `mistralai/Mistral-7B-Instruct-v0.3` |

Configure via variáveis de ambiente:

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=sua_chave
# ou OPENAI_API_KEY, ANTHROPIC_API_KEY, HUGGINGFACE_API_KEY
```

### 🤗 Modelos Open-Source HuggingFace

> O provider HuggingFace usa `chat_completion` (OpenAI-compatible) com **detecção automática de tool calling**: modelos que suportam function calling nativo recebem `tools=[...]` direto na API; os demais usam prompt injection como fallback. Use `hf_model_supports_tools(model_id)` para verificar.



O Mangaba inclui um catálogo de **28 modelos open-source** disponíveis via HuggingFace Inference API, organizados por categoria:

```python
from mangaba import list_huggingface_models, HF_OPEN_MODELS

# Listar todos os modelos
todos = list_huggingface_models()

# Filtrar por categoria: general, code, reasoning, embedding
modelos_codigo  = list_huggingface_models(category="code")
modelos_reason  = list_huggingface_models(category="reasoning")
modelos_embed   = list_huggingface_models(category="embedding")

# Via classe do provider
from mangaba.core.llm.client import HuggingFaceLLMProvider
HuggingFaceLLMProvider.list_models(category="general")
```

| Categoria | Modelos incluídos |
|---|---|
| **general** (19) | Mistral 7B/Mixtral 8x7B/8x22B, Llama 3/3.1/3.2, Qwen 2.5, Phi-3/3.5, Gemma 2 |
| **code** (4) | StarCoder2 15B, Qwen 2.5 Coder 7B/32B, DeepSeek Coder 33B |
| **reasoning** (2) | DeepSeek R1 Distill Qwen 7B, DeepSeek R1 Distill Llama 70B |
| **embedding** (3) | BGE-M3, all-MiniLM-L6-v2, Multilingual E5 Large |

Cada modelo expõe: `id`, `name`, `category`, `context` (tokens), `tool_calling`, `streaming`, `notes`.

```python
from mangaba import hf_model_supports_tools

hf_model_supports_tools("mistralai/Mistral-7B-Instruct-v0.3")  # True  — nativo
hf_model_supports_tools("google/gemma-2-9b-it")                # False — prompt injection
```

## 🧪 Testes

```bash
# Testes v3 (32 testes)
python -m pytest tests/test_v3.py -v

# Todos os testes
python -m pytest tests/ -v

# Com cobertura
python -m pytest tests/ --cov=mangaba --cov-report=term-missing
```

## 📦 Dependências

**Core:**
- `pydantic>=2.0.0` — Validação de tipos
- `google-generativeai>=0.3.0` — Google Gemini
- `openai>=1.6.0` — OpenAI GPT
- `anthropic>=0.20.0` — Anthropic Claude
- `huggingface-hub>=0.20.0` — HuggingFace
- `tiktoken>=0.5.0` — Contagem de tokens
- `requests>=2.25.0` — HTTP client
- `loguru>=0.6.0` — Logging

**Opcionais:**
- `numpy>=1.24.0` — RAG e embeddings (`pip install mangaba[rag]`)
- `duckduckgo-search>=3.9.0` — Busca web (`pip install mangaba[tools]`)

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License

---

**Mangaba AI v3.0** — Framework profissional de agentes IA 🥭🤖
