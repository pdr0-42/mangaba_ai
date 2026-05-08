# 🥭 Mangaba AI — Documentação Completa

> **Professional multi-agent orchestration framework with ReAct reasoning, RAG, memory, and function calling.**

**Versão:** 3.2.0 | **Licença:** MIT | **Python:** ≥3.9

---

## 📚 Índice

| Seção | Descrição |
|---|---|
| [Home](docs/Home.md) | Visão geral e introdução |
| [Getting Started](docs/Getting-Started.md) | Instalação e primeiro projeto |
| [Core Components](docs/Core-Components.md) | Agent, Task, Crew |
| [LLM Providers](docs/LLM-Providers.md) | Google, OpenAI, Anthropic, HuggingFace, OpenRouter |
| [Tools](docs/Tools.md) | Sistema de ferramentas |
| [Memory](docs/Memory.md) | Short-term, Long-term, Entity |
| [RAG](docs/RAG.md) | Retrieval-Augmented Generation |
| [Vector Stores](docs/Vector-Stores.md) | InMemory, Redis, PostgreSQL |
| [Workflows](docs/Workflows.md) | Pipeline, Stage, ParallelStage |
| [Events](docs/Events.md) | EventBus e Callbacks |
| [Guardrails](docs/Guardrails.md) | Validação de entrada/saída |
| [Protocols](docs/Protocols.md) | A2A e MCP |
| [API Reference](docs/API-Reference.md) | Referência completa da API |
| [Examples](docs/Examples.md) | Exemplos práticos |

---

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────┐
│                    Mangaba AI Framework                  │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  Agent   │  Crew    │ Workflow │  RAG     │  Protocols  │
│  (ReAct) │(Orchestr)│(Pipeline)│(Retrieval)│ (A2A/MCP)  │
├──────────┴──────────┴──────────┴──────────┴─────────────┤
│                    Core Engine                           │
│  ┌────────┐ ┌──────┐ ┌───────┐ ┌────────┐ ┌──────────┐ │
│  │  LLM   │ │Tools │ │Memory │ │Events  │ │Guardrails│ │
│  │Client  │ │System│ │System │ │ Bus    │ │ Parsers  │ │
│  └────────┘ └──────┘ └───────┘ └────────┘ └──────────┘ │
├─────────────────────────────────────────────────────────┤
│              LLM Providers (5 backends)                  │
│  Google  │  OpenAI  │  Anthropic  │  HF  │  OpenRouter  │
├─────────────────────────────────────────────────────────┤
│              Vector Stores (3 backends)                  │
│  InMemory  │  Redis (RediSearch)  │  PostgreSQL(pgvector)│
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Recursos Principais

| Recurso | Descrição |
|---|---|
| **Multi-Agent** | Orquestre múltiplos agents com 4 modos: Sequential, Hierarchical, Parallel, Consensual |
| **ReAct Reasoning** | Thought → Action → Observation loop para uso inteligente de ferramentas |
| **5 LLM Providers** | Google Gemini, OpenAI, Anthropic Claude, HuggingFace, OpenRouter |
| **Function Calling** | Tool use nativo em todos os providers |
| **RAG** | Pipeline completo: loaders, splitters, retriever, chain |
| **3 Vector Stores** | InMemory, Redis (RediSearch HNSW), PostgreSQL (pgvector) |
| **Memory** | Short-term (sliding window), Long-term (SQLite), Entity |
| **Workflows** | Pipeline com Stage, ParallelStage, ConditionalStage |
| **Event Bus** | Sistema de eventos para observabilidade e logging |
| **Guardrails** | Validação de entrada/saída com cadeias de guardrails |
| **A2A Protocol** | Agent-to-Agent communication |
| **MCP Protocol** | Model Context Protocol integration |
| **Streaming** | Suporte a streaming em todos os providers |
| **Caching** | Cache de respostas LLM (InMemory, Disk) |
| **Retry** | Retry automático com backoff exponencial |

---

## 🚀 Quick Start

```python
from mangaba import Agent, Task, Crew, Process
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# 1. Configuração via LLMConfig
llm_config = LLMConfig(
    provider="google",
    model="gemini-2.5-flash",
    api_key="YOUR_KEY",
    temperature=0.7,
    max_tokens=4096,
)

llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# 2. Create agent
researcher = Agent(
    role="Senior Researcher",
    goal="Discover cutting-edge developments in AI",
    backstory="Expert AI researcher with deep knowledge of the field",
    llm=llm,
    verbose=True,
)

# 3. Create task
task = Task(
    description="Research the latest trends in AI agents for 2026",
    expected_output="A comprehensive report with 10 key findings",
    agent=researcher,
)

# 4. Create crew and run
crew = Crew(
    agents=[researcher],
    tasks=[task],
    process=Process.SEQUENTIAL,
)
result = crew.kickoff()
print(result)
```

---

## 📦 Instalação

```bash
# Instalar via pip
pip install mangaba

# Com RAG support
pip install mangaba[rag]

# Com Redis vector store
pip install mangaba[redis]

# Com PostgreSQL vector store
pip install mangaba[postgres]

# Todas as dependências
pip install mangaba[all]
```

---

## 📁 Estrutura do Projeto

```
mangaba_ai/
├── mangaba/                    # Main package
│   ├── __init__.py             # Public API exports
│   ├── core/                   # Core framework
│   │   ├── agent.py            # Agent with ReAct reasoning
│   │   ├── task.py             # Task definitions
│   │   ├── crew.py             # Multi-agent orchestration
│   │   ├── workflow.py         # Pipeline engine
│   │   ├── events.py           # Event bus & callbacks
│   │   ├── reasoning.py        # ReAct engine
│   │   ├── guardrails.py       # Input/output validation
│   │   ├── output_parsers.py   # JSON, Pydantic parsers
│   │   ├── planner.py          # Task planning
│   │   ├── types.py            # Pydantic models
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── llm/                # LLM providers
│   │       ├── client.py       # Multi-provider engine
│   │       ├── cache.py        # Response caching
│   │       ├── retry.py        # Retry logic
│   │       ├── token_counter.py# Token tracking
│   │       └── prompt_templates.py
│   ├── tools/                  # Tool system
│   │   ├── base.py             # BaseTool abstract class
│   │   ├── decorator.py        # @tool decorator
│   │   ├── toolkit.py          # Tool collections
│   │   ├── math_tools.py       # Calculator
│   │   ├── text_tools.py       # Text utilities
│   │   ├── file_tools.py       # File operations
│   │   └── web_search.py       # Web search
│   ├── memory/                 # Memory systems
│   │   ├── base.py             # BaseMemory abstract class
│   │   ├── short_term.py       # Sliding window
│   │   ├── long_term.py        # SQLite + vector search
│   │   └── entity.py           # Entity tracking
│   ├── embeddings/             # Embedding providers
│   │   ├── base.py             # BaseEmbedding interface
│   │   ├── openai_embed.py     # OpenAI embeddings
│   │   └── google_embed.py     # Google embeddings
│   ├── vectorstores/           # Vector stores
│   │   ├── base.py             # BaseVectorStore interface
│   │   ├── in_memory.py        # Pure Python implementation
│   │   ├── redis.py            # Redis Stack (RediSearch)
│   │   ├── postgres.py         # PostgreSQL (pgvector)
│   │   └── factory.py          # create_vectorstore()
│   ├── rag/                    # RAG pipeline
│   │   ├── document.py         # Document model
│   │   ├── loaders.py          # Text, CSV loaders
│   │   ├── splitters.py        # Text splitting
│   │   ├── retriever.py        # Embedding + vector store
│   │   └── chain.py            # RAG chain for Q&A
│   └── callbacks/              # Observability
├── protocols/                  # Communication protocols
│   ├── a2a.py                  # Agent-to-Agent protocol
│   └── mcp.py                  # Model Context Protocol
├── examples/                   # Example scripts
├── tests/                      # Test suite
├── docs/                       # Documentation (this wiki)
├── pyproject.toml              # Project config
└── docker-compose.vectorstores.yml
```
