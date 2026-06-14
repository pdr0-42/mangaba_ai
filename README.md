<div align="center">
  <img src="assets/mangaba-logo.svg" alt="Mangaba AI" width="140"/>

  [![Mangaba AI](https://img.shields.io/badge/Mangaba-AI-F97518?style=for-the-badge)](https://www.mangaba.ia.br)
  [![Site](https://img.shields.io/badge/mangaba.ia.br-1E0D01?style=for-the-badge)](https://www.mangaba.ia.br)
</div>

# 🥭 Mangaba AI

[![PyPI version](https://img.shields.io/pypi/v/mangaba.svg)](https://pypi.org/project/mangaba/)
[![Python](https://img.shields.io/pypi/pyversions/mangaba.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/Mangaba-ai/mangaba_ai/actions)

**Framework profissional de orquestração multi-agente** com ReAct reasoning, function calling nativo, RAG, memória persistente, protocolos A2A/MCP, vector stores avançadas e suporte resiliente a múltiplos provedores LLM.

> Alternativa leve e completa a CrewAI + LangChain em um único pacote, com interoperabilidade real entre provedores, arquitetura resiliente e comunicação entre agentes via protocolos padrão.

## ✨ Destaques v3.3.0

- 🤝 **Protocolos A2A & MCP** — Agent-to-Agent messaging com request/response/broadcast + Multi-Context Protocol para contextos hierárquicos entre agentes
- 🗄️ **Vector Stores Avançadas** — ChromaDB, PostgreSQL+pgvector, Redis+RediSearch, SQLite + factory `create_vectorstore()` para troca transparente
- 🧩 **Prompt Templates** — `PromptTemplate`, `ChatPromptTemplate`, `SystemPromptBuilder` para engenharia de prompt reutilizável
- 📋 **Task Planner** — Decomposição automática de tarefas complexas em planos de execução com dependências
- 🧰 **Toolkits** — Agrupamento lógico de ferramentas com `BaseToolkit`, `FileToolkit`, `WebToolkit`
- 🤗 **HuggingFace Embeddings** — Sentence-transformers como terceiro provedor de embedding
- 👤 **Entity Memory** — Rastreamento de entidades e relacionamentos entre interações
- 📊 **UsageTracker** — Controle acumulativo de tokens por provedor em toda a execução
- ⚙️ **Config System** — Configuração unificada via `Config` class com suporte a `.env` e JSON
- 🔄 **CallbackManager** — Gerencie callbacks customizados com filtro por tipo de evento

### Features consolidadas (desde v3.0)

- 🚀 **OpenRouter Native Support** — Roteamento dinâmico com fallback automático entre modelos
- 🔄 **Multi-Provider Interoperability** — Misture agentes de diferentes provedores (ex: Gemini + Llama) na mesma Crew
- 🧠 **ReAct Reasoning** — Loop Thought→Action→Observation com function calling nativo
- 🤖 **5 Provedores LLM** — Google Gemini, OpenAI GPT, Anthropic Claude, HuggingFace e OpenRouter
- 👥 **4 Processos de Crew** — Sequential, Hierarchical, Parallel (asyncio), Consensual
- 🔧 **Tool System** — `@tool` decorator, Pydantic schemas, JSON schema automático para LLM
- 📚 **RAG Pipeline** — Document loaders, text splitters, embeddings, vector store, retriever
- 💾 **Memória** — Curto prazo (sliding window), longo prazo (SQLite), entidades
- 🛡️ **Guardrails** — Validação de tamanho, filtro de conteúdo, schema validation
- 📊 **Observabilidade** — EventBus com 22+ tipos de evento, callbacks console/arquivo
- 🔄 **Workflow Engine** — Pipelines com stages sequenciais, paralelos e condicionais
- ⚡ **Cache & Retry** — Cache LRU + disco (SQLite), retry com backoff exponencial + fallback automático

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
from mangaba.core import Agent, Task, Crew, Process, tool
from mangaba.core.types import LLMConfig

@tool
def search(query: str) -> str:
    """Search the web for information."""
    return f"Results for: {query}"

researcher = Agent(
    role="Research Analyst",
    goal="Find accurate information",
    backstory="Expert researcher with 10 years of experience",
    tools=[search],
    llm_config=LLMConfig(provider="google", model="gemini-2.5-flash", api_key="sua-chave"),
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

### Multi-Provider Crew com fallback

```python
from mangaba.core import Agent, Task, Crew
from mangaba.core.crew import Process
from mangaba.core.types import OpenRouterConfig, LLMConfig

pesquisador = Agent(
    role="Pesquisador",
    goal="Analisar vulnerabilidades",
    llm_config=OpenRouterConfig(
        provider="openrouter",
        model=[
            "google/gemini-2.5-flash",
            "anthropic/claude-3.5-sonnet"
        ],
        api_key="SUA_KEY"
    )
)

revisor = Agent(
    role="Revisor",
    goal="Revisar análise técnica",
    llm_config=LLMConfig(
        provider="hf",
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        api_key="SUA_KEY"
    )
)

task = Task(
    description="Explique buffer overflow",
    expected_output="Análise técnica detalhada",
    agent=pesquisador,
)

review = Task(
    description="Revise a análise",
    expected_output="Pontos fortes e fracos",
    agent=revisor,
)

crew = Crew(
    agents=[pesquisador, revisor],
    tasks=[task, review],
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

docs = TextLoader("data.txt").load()
chunks = RecursiveTextSplitter(chunk_size=500).split_documents(docs)

embedding = OpenAIEmbedding(api_key="YOUR_KEY")
store = InMemoryVectorStore(embedding)
store.add(chunks)
retriever = Retriever(embedding=embedding, vector_store=store)

from mangaba.core.llm import create_llm_client
llm = create_llm_client(provider="google", api_key="YOUR_KEY")
chain = RAGChain(llm=llm, retriever=retriever)
answer = chain.query("What are the main topics?")
```

### Memória persistente

```python
from mangaba.memory import ShortTermMemory, LongTermMemory

short = ShortTermMemory(max_items=50)
short.add("User asked about Python")

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

### Comunicação entre agentes (A2A Protocol — NOVO v3.3.0)

```python
from protocols.a2a import A2AProtocol, A2AMessage

protocolo = A2AProtocol()

# Enviar mensagem de um agente para outro
msg = A2AMessage(
    sender="pesquisador",
    recipient="revisor",
    content="Análise de vulnerabilidade concluída",
    msg_type="request"
)
protocolo.send(msg)

# Broadcast para todos os agentes
protocolo.broadcast(A2AMessage(
    sender="manager",
    recipient="*",
    content="Iniciando nova tarefa",
    msg_type="broadcast"
))
```

### Vector store com ChromaDB (NOVO v3.3.0)

```python
from mangaba.vectorstores import ChromaVectorStore, create_vectorstore
from mangaba.embeddings import OpenAIEmbedding

embedding = OpenAIEmbedding(api_key="KEY")

# Via factory
store = create_vectorstore("chroma", embedding=embedding, persist_directory="./chroma_db")

# Adicionar e buscar
store.add(chunks)
results = store.similarity_search("machine learning", k=5)
```

## 🗄️ Vector Stores

| Store | Persistência | Ideal para |
|---|---|---|
| **InMemoryVectorStore** | Volátil (RAM) | Testes e protótipos |
| **ChromaVectorStore** | Disco (ChromaDB) | Aplicações standalone |
| **PostgresVectorStore** | PostgreSQL + pgvector | Produção, dados relacionais |
| **RedisVectorStore** | Redis + RediSearch | Alta performance, caching |
| **SQLiteVectorStore** | SQLite local | Embeddings simples, sem infra |

Todas implementam `BaseVectorStore` e são intercambiáveis via `create_vectorstore()`.

## 🤝 Protocolos de Comunicação

### A2A (Agent-to-Agent)
Mensageria direta entre agentes com suporte a request/response e broadcast:

```python
from protocols.a2a import A2AProtocol, A2AMessage

protocol = A2AProtocol()
protocol.send(A2AMessage(sender="agent_a", recipient="agent_b", content="..."))
```

### MCP (Multi-Context Protocol)
Compartilhamento de contexto hierárquico entre agentes com prioridade, tags e busca por relevância:

```python
from protocols.mcp import MCPProtocol, MCPContext

mcp = MCPProtocol()
ctx = MCPContext(content="Dados da análise", priority=8, tags=["analise", "vulnerabilidade"])
mcp.share_context("sessao_1", ctx)
resultados = mcp.query_context("sessao_1", "vulnerabilidade")
```

## 🧩 Prompt Templates

```python
from mangaba.core.llm.prompt_templates import PromptTemplate, ChatPromptTemplate, SystemPromptBuilder

# Template simples
template = PromptTemplate("Responda em {idioma}: {pergunta}")
result = template.format(idioma="português", pergunta="o que é IA?")

# Template de chat
chat = ChatPromptTemplate([
    ("system", "Você é um especialista em {topico}"),
    ("user", "{pergunta}"),
])
messages = chat.format_messages(topico="segurança", pergunta="O que é XSS?")

# Builder pattern
builder = SystemPromptBuilder()
builder.add_role("Analista de Segurança")
builder.add_context("Você trabalha com pentest há 10 anos")
builder.add_instruction("Responda em markdown")
prompt = builder.build()
```

## 🏛️ Padrões de Projeto

O Mangaba aplica padrões GoF de forma consistente em toda a base de código:

| Padrão | Onde é usado |
|---|---|
| **Factory** | `create_llm_client()` / `create_vectorstore()` — instancia provedores por nome |
| **Abstract Factory** | `BaseLLMProvider` / `BaseVectorStore` — interface comum; cada provider é uma família concreta |
| **Facade** | `LLMClient` — esconde a complexidade dos provedores atrás de uma API uniforme |
| **Decorator** | `@tool` — converte funções Python em `BaseTool` com schema automático |
| **Composite** | `Crew` / `Toolkit` — agrega múltiplos agentes/tarefas/ferramentas como unidade |
| **Strategy** | `Process` (sequential/hierarchical/parallel/consensual); providers como strategies |
| **Observer** | `EventBus` + callbacks (`ConsoleCallback`, `FileCallback`) |
| **Template Method** | `BaseLLMProvider.generate/stream/generate_with_tools` — subclasses implementam os passos |
| **Chain of Responsibility** | `GuardrailChain` — passa o output por validadores em sequência |
| **Command** | `Task` — encapsula instrução, agente e ferramentas |
| **Iterator** | `stream()` — retorna `Iterator[str]` token a token |
| **Pipes & Filters** | `Pipeline → Stage[] → ParallelStage / ConditionalStage` |
| **Builder** | `SystemPromptBuilder` — constrói system prompts passo a passo |
| **Singleton** | `EventBus` — instância única de barramento de eventos |

## 🏗️ Arquitetura

```
mangaba/
├── core/                   # Cérebro do framework
│   ├── agent.py                # Agent com ReAct reasoning
│   ├── task.py                 # Tasks com guardrails e retry
│   ├── crew.py                 # Orquestração (4 processos)
│   ├── workflow.py             # Pipeline engine
│   ├── reasoning.py            # ReAct loop (Think→Act→Observe)
│   ├── planner.py              # Decomposição automática de tarefas
│   ├── guardrails.py           # LengthGuardrail, ContentFilter, Schema
│   ├── output_parsers.py       # JSON, Pydantic, List, Markdown
│   ├── types.py                # Tipos Pydantic v2 (LLMConfig, AgentState...)
│   ├── exceptions.py           # Hierarquia de 19+ exceções
│   ├── events.py               # EventBus (22+ event types)
│   └── llm/                    # Engine LLM multi-provider
│       ├── client.py               # 5 providers + OpenRouter + fallback
│       ├── retry.py                # Retry com backoff exponencial
│       ├── cache.py                # LRU (memória) + SQLite (disco)
│       ├── token_counter.py        # TokenCounter + UsageTracker
│       └── prompt_templates.py     # PromptTemplate, ChatPromptTemplate, SystemPromptBuilder
├── tools/                  # Sistema de ferramentas
│   ├── base.py                 # BaseTool + JSON schema automático
│   ├── decorator.py            # @tool decorator
│   ├── toolkit.py              # BaseToolkit, FileToolkit, WebToolkit
│   ├── file_tools.py           # FileReader, FileWriter, DirectoryList
│   ├── web_search.py           # Serper, DuckDuckGo
│   ├── math_tools.py           # Calculadora segura (AST)
│   └── text_tools.py           # TextSplitter, WordCounter
├── memory/                 # Sistema de memória
│   ├── base.py                 # BaseMemory ABC
│   ├── short_term.py           # Sliding window (deque)
│   ├── long_term.py            # SQLite + embeddings opcionais
│   └── entity.py               # Memória de entidades
├── embeddings/             # Provedores de embedding
│   ├── base.py                 # BaseEmbedding ABC
│   ├── openai_embed.py         # text-embedding-3-small
│   ├── google_embed.py         # text-embedding-004
│   └── huggingface_embed.py    # Sentence-transformers
├── vectorstores/           # Armazenamento vetorial
│   ├── base.py                 # BaseVectorStore ABC
│   ├── factory.py              # create_vectorstore() + register_store()
│   ├── in_memory.py            # Cosine similarity (numpy)
│   ├── chroma_db.py            # ChromaDB
│   ├── postgres.py             # PostgreSQL + pgvector
│   ├── redis.py                # Redis + RediSearch
│   └── sqlite.py               # SQLite vector store
├── rag/                    # Pipeline RAG
│   ├── document.py             # Modelo de documento
│   ├── loaders.py              # Text, CSV
│   ├── splitters.py            # RecursiveTextSplitter
│   ├── retriever.py            # Embedding + vector store
│   └── chain.py                # RAGChain com fontes
├── callbacks/              # Observabilidade
│   ├── console.py              # Print formatado de eventos
│   └── file.py                 # Log JSONL
├── __init__.py              # API pública do pacote
├── config.py                # Config system (leituta .env)
└── exceptions.py            # (legado)

protocols/                 # Protocolos de comunicação entre agentes
├── a2a.py                     # Agent-to-Agent protocol
└── mcp.py                     # Multi-Context Protocol

utils/                     # Utilitários
└── logger.py                  # Logger colorido (Loguru)

docs/                       # Documentação completa
├── API-Reference.md
├── CHANGELOG.md
├── Core-Components.md
├── Events.md
├── Guardrails.md
├── LLM-Providers.md
├── Memory.md
├── RAG.md
├── Tools.md
├── Vector-Stores.md
├── Workflows.md
├── Getting-Started.md
├── CURSO_BASICO.md
├── Examples.md
├── FAQ.md
└── ...

examples/                  # Exemplos práticos
├── basic_example.py
├── crew_example.py
├── finance_example.py
├── legal_example.py
├── medical_example.py
├── marketing_example.py
├── text_analysis_example.py
├── translation_example.py
├── document_analysis_example.py
├── vectorstores_example.py
└── ...
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
| **OpenRouter** | ✅ Nativo + Fallback | ✅ | Multi-model routing |
| **Google Gemini** | ✅ Nativo | ✅ | `gemini-2.5-flash` |
| **OpenAI** | ✅ Nativo | ✅ | `gpt-4o-mini` |
| **Anthropic** | ✅ Nativo (tool_use) | ✅ | `claude-3-haiku-20240307` |
| **HuggingFace** | ✅ Nativo (11 modelos) / ⚠️ Prompt (14 modelos) | ✅ via `chat_completion` | `mistralai/Mistral-7B-Instruct-v0.3` |

Configure via variáveis de ambiente:

```env
LLM_PROVIDER=google
GOOGLE_API_KEY=sua_chave
# ou OPENAI_API_KEY, ANTHROPIC_API_KEY, HUGGINGFACE_API_KEY, OPENROUTER_API_KEY
```

### 🤗 Modelos Open-Source HuggingFace

O provider HuggingFace usa `chat_completion` (OpenAI-compatible) com **detecção automática de tool calling**: modelos que suportam function calling nativo recebem `tools=[...]` direto na API; os demais usam prompt injection como fallback. Use `hf_model_supports_tools(model_id)` para verificar.

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

```python
from mangaba import hf_model_supports_tools

hf_model_supports_tools("mistralai/Mistral-7B-Instruct-v0.3")  # True  — nativo
hf_model_supports_tools("google/gemma-2-9b-it")                # False — prompt injection
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
- `sentence-transformers>=2.2.0` — Embeddings HF (`pip install mangaba[embeddings]`)
- `duckduckgo-search>=3.9.0` — Busca web (`pip install mangaba[tools]`)
- `redis>=5.0.0` — Redis vector store (`pip install mangaba[redis]`)
- `psycopg[binary]>=3.1.0` — Postgres vector store (`pip install mangaba[postgres]`)
- `chromadb>=0.4.0` — ChromaDB vector store (`pip install mangaba[chroma]`)
- **Tudo:** `pip install mangaba[all]`

## 🧪 Testes

```bash
# Testes v3
python -m pytest tests/test_v3.py -v

# Todos os testes (14 suites)
python -m pytest tests/ -v

# Com cobertura (mínimo 80%)
python -m pytest tests/ --cov=mangaba --cov-report=term-missing
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/nova-feature`)
3. Commit (`git commit -m 'Add nova feature'`)
4. Push (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

MIT License

---
