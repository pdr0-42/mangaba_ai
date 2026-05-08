# 📖 API Reference

Referência completa de todas as classes, métodos e funções públicas.

---

## mangaba (Top-level)

```python
from mangaba import (
    # Core
    Agent,
    Task,
    Crew,
    Process,
    # Workflow
    Pipeline,
    Stage,
    ParallelStage,
    ConditionalStage,
    # LLM
    LLMClient,
    create_llm_client,
    list_huggingface_models,
    hf_model_supports_tools,
    HF_OPEN_MODELS,
    # Events
    EventBus,
    Event,
    EventType,
    # Reasoning
    ReActEngine,
    # Guardrails & Parsers
    GuardrailChain,
    JSONOutputParser,
    PydanticOutputParser,
    # Tools
    BaseTool,
    tool,
    # Exceptions
    MangabaError,
)
```

---

## Core

### Agent

```python
class Agent:
    def __init__(
        self,
        role: str,
        goal: str,
        backstory: str,
        tools: Optional[List[BaseTool]] = None,
        llm: Optional[Any] = None,
        llm_config: Optional[LLMConfig] = None,
        api_key: Optional[str] = None,
        verbose: bool = False,
        memory: Optional[BaseMemory] = None,
        memory_config: Optional[MemoryConfig] = None,
        max_iterations: int = 15,
        max_retry_on_error: int = 3,
        allow_delegation: bool = True,
        step_callback: Optional[Callable] = None,
        guardrails: Optional[List[BaseGuardrail]] = None,
        output_parser: Optional[BaseOutputParser] = None,
        agent_id: Optional[str] = None,
    )
    def execute_task(self, task_description: str, context: Optional[str] = None) -> str
    def connect_to(self, other: Agent) -> None
    def delegate(self, peer_id: str, task_description: str, context: Optional[str] = None) -> str
```

### Task

```python
class Task:
    def __init__(
        self,
        description: str,
        expected_output: str,
        agent: Optional[Agent] = None,
        context: Optional[List[Task]] = None,
        tools: Optional[List[BaseTool]] = None,
        output_file: Optional[str] = None,
        callback: Optional[Callable] = None,
        async_execution: bool = False,
        human_input: bool = False,
        guardrails: Optional[List[BaseGuardrail]] = None,
        output_parser: Optional[BaseOutputParser] = None,
        retry_on_failure: int = 0,
        task_id: Optional[str] = None,
    )
    def execute(self, inputs: Optional[Dict[str, Any]] = None) -> TaskOutput
    async def aexecute(self, inputs: Optional[Dict[str, Any]] = None) -> TaskOutput
```

### TaskOutput

```python
class TaskOutput:
    description: str
    result: str
    agent: str
    success: bool
    timestamp: str
```

### Crew

```python
class Crew:
    def __init__(
        self,
        agents: List[Agent],
        tasks: List[Task],
        process: Process = Process.SEQUENTIAL,
        verbose: bool = False,
        max_rpm: Optional[int] = None,
        memory: Optional[Any] = None,
        crew_id: Optional[str] = None,
    )
    def kickoff(self, inputs: Optional[Dict[str, Any]] = None) -> CrewOutput
```

### CrewOutput

```python
class CrewOutput:
    tasks_outputs: List[TaskOutput]
    process: Process
    duration: float
    crew_id: str
    timestamp: str
    @property
    def final_output(self) -> str
```

### Process (Enum)

```python
class Process(Enum):
    SEQUENTIAL = "sequential"
    HIERARCHICAL = "hierarchical"
    PARALLEL = "parallel"
    CONSENSUAL = "consensual"
```

---

## LLM

### create_llm_client

```python
def create_llm_client(
    provider: str,
    api_key: str,
    model: str,
    temperature: float = 0.7,
    max_output_tokens: int = 4096,
    **options: Any,
) -> LLMClient
```

### LLMClient

```python
class LLMClient:
    def __init__(self, provider: str, api_key: str, model: str, **options: Any)
    def generate(self, prompt: str, **kwargs) -> LLMResponse
    def generate_with_tools(self, messages: List[dict], tools: List[BaseTool]) -> LLMResponse
    def stream(self, prompt: str, **kwargs) -> Iterator[str]
```

### LLMResponse

```python
class LLMResponse:
    text: str
    tool_calls: List[ToolCall]
    has_tool_calls: bool
    finish_reason: FinishReason
    usage: TokenUsage
    model: str
```

### Providers

| Class | Name | Aliases |
|---|---|---|
| `GoogleLLMProvider` | `google` | `gemini` |
| `OpenAILLMProvider` | `openai` | — |
| `AnthropicLLMProvider` | `anthropic` | `claude` |
| `HuggingFaceLLMProvider` | `huggingface` | `hf` |
| `OpenRouterLLMProvider` | `openrouter` | — |

### Cache

```python
class InMemoryCache(LLMCache):
    def __init__(self, ttl: int = 3600)

class DiskCache(LLMCache):
    def __init__(self, cache_dir: str = "./llm_cache", ttl: int = 86400)
```

### Retry

```python
def with_retry(max_retries: int = 3, backoff_factor: int = 2)
```

### Token Tracking

```python
class TokenCounter:
    def count_tokens(self, text: str) -> int

class UsageTracker:
    @property
    def total_tokens(self) -> int
    def estimated_cost(self) -> float
    @property
    def history(self) -> List[TokenUsage]
```

### Prompt Templates

```python
class PromptTemplate:
    def __init__(self, template: str, input_variables: Set[str])
    def format(self, **kwargs) -> str

class ChatPromptTemplate:
    def add_system(self, text: str) -> None
    def add_user(self, text: str, **variables) -> None
    def format_messages(self, **kwargs) -> List[dict]

class SystemPromptBuilder:
    def set_role(self, role: str) -> Self
    def set_goal(self, goal: str) -> Self
    def add_instruction(self, instruction: str) -> Self
    def build(self) -> str
```

---

## Tools

### BaseTool

```python
class BaseTool:
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]]
    return_direct: bool

    def run(self, **kwargs: Any) -> Any
    def _run(self, **kwargs: Any) -> Any  # Override in subclasses
    def get_function_schema(self) -> Dict[str, Any]
```

### @tool Decorator

```python
@tool
def my_tool(arg1: str, arg2: int = 10) -> str:
    """Description of the tool."""
    return f"{arg1}: {arg2}"
```

### Built-in Tools

| Tool | Description |
|---|---|
| `CalculatorTool` | Evaluate mathematical expressions |
| `TextSplitterTool` | Split text into chunks |
| `WordCounterTool` | Count words and sentences |

### Toolkits

```python
class BaseToolkit:
    @property
    def tools(self) -> List[BaseTool]

class FileToolkit(BaseToolkit)
class WebToolkit(BaseToolkit)
```

---

## Memory

### BaseMemory

```python
class BaseMemory:
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]
    def get_all(self) -> List[Dict[str, Any]]
    def clear(self) -> None
    def get_relevant(self, query: str, max_results: int = 5) -> str
```

### Implementations

| Class | Persistence | Search | Max Items |
|---|---|---|---|
| `ShortTermMemory` | ❌ | Keyword | Configurable |
| `LongTermMemory` | ✅ SQLite | Vector + Keyword | Unlimited |
| `EntityMemory` | ❌ | Entity-based | Unlimited |

---

## Embeddings

### BaseEmbedding

```python
class BaseEmbedding:
    def embed_text(self, text: str) -> List[float]
    def embed_batch(self, texts: List[str]) -> List[List[float]]
```

### Implementations

| Class | Model | Dimensions |
|---|---|---|
| `OpenAIEmbedding` | `text-embedding-3-small` | 1536 |
| `GoogleEmbedding` | `text-embedding-004` | 768 |

---

## Vector Stores

### BaseVectorStore

```python
class BaseVectorStore:
    def add(self, texts: List[str], embeddings: List[List[float]], metadatas: Optional[List[Dict[str, Any]]] = None) -> List[str]
    def search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]
    def delete(self, ids: List[str]) -> None
    def clear(self) -> None
    @property
    def count(self) -> int
```

### Implementations

| Class | Backend | Index |
|---|---|---|
| `InMemoryVectorStore` | Python list | Cosine (manual) |
| `RedisVectorStore` | Redis Stack | HNSW (RediSearch) |
| `PostgresVectorStore` | PostgreSQL | HNSW (pgvector) |

### Factory

```python
def create_vectorstore(store_type: str, **kwargs: Any) -> BaseVectorStore
def get_supported_stores() -> tuple[str, ...]
def register_store(name: str, cls: Type[BaseVectorStore]) -> None
```

---

## RAG

### Document

```python
class Document:
    content: str
    metadata: Dict[str, Any]
```

### Loaders

| Class | Description |
|---|---|
| `TextLoader` | Load .txt files |
| `CSVLoader` | Load .csv files |

### Splitter

```python
class RecursiveTextSplitter:
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50)
    def split_text(self, text: str) -> List[str]
    def split_documents(self, documents: List[Document]) -> List[Document]
```

### Retriever

```python
class Retriever:
    def __init__(self, embedding: BaseEmbedding, store: BaseVectorStore)
    def add_documents(self, documents: List[Document]) -> List[str]
    def search(self, query: str, top_k: int = 5) -> List[Document]
    def clear(self) -> None
```

### RAGChain

```python
class RAGChain:
    def __init__(self, llm: LLMClient, retriever: Retriever, top_k: int = 3)
    def ask(self, question: str) -> str
```

---

## Workflows

### Stage

```python
class Stage:
    def __init__(self, name: str, tasks: List[Task])
    def run(self, inputs: Dict[str, Any]) -> StageResult
```

### ParallelStage

```python
class ParallelStage(Stage):
    def run(self, inputs: Dict[str, Any]) -> StageResult  # Async
```

### ConditionalStage

```python
class ConditionalStage:
    def __init__(
        self,
        name: str,
        condition: Callable[[Dict[str, Any]], bool],
        if_true: Stage,
        if_false: Optional[Stage] = None,
    )
    def run(self, inputs: Dict[str, Any]) -> StageResult
```

### Pipeline

```python
class Pipeline:
    def __init__(self, stages: list, name: str = "pipeline")
    def run(self, inputs: Optional[Dict[str, Any]] = None) -> PipelineResult
```

### PipelineResult

```python
class PipelineResult:
    stages: List[StageResult]
    duration: float
    @property
    def final_output(self) -> str
```

### StageResult

```python
class StageResult:
    stage_name: str
    outputs: List[TaskOutput]
    duration: float
```

---

## Events

### EventType (Enum)

See [Events documentation](Events.md) for full list.

### Event

```python
class Event(BaseModel):
    event_type: EventType
    data: Dict[str, Any]
    source_id: str
    source_type: str
    timestamp: str
    parent_event_id: Optional[str]
    trace_id: Optional[str]
```

### EventBus

```python
class EventBus:
    @classmethod
    def register(cls, handler: BaseCallback | Callable, event_types: Optional[Set[EventType]] = None)
    @classmethod
    def unregister(cls, handler: BaseCallback)
    @classmethod
    def emit(cls, event: Event)
    @classmethod
    def reset(cls)
```

### BaseCallback

```python
class BaseCallback(ABC):
    event_filter: Optional[Set[EventType]] = None
    def should_handle(self, event: Event) -> bool
    def on_event(self, event: Event) -> None
```

---

## Guardrails

### BaseGuardrail

```python
class BaseGuardrail(ABC):
    def validate(self, text: str) -> str
```

### Implementations

| Class | Description |
|---|---|
| `LengthGuardrail` | Min/max length validation |
| `ContentFilterGuardrail` | Block/redact patterns |
| `SchemaGuardrail` | Pydantic schema validation |
| `GuardrailChain` | Chain multiple guardrails |

---

## Output Parsers

### BaseOutputParser

```python
class BaseOutputParser(ABC):
    def parse(self, text: str) -> Any
    def get_format_instructions(self) -> str
```

### Implementations

| Class | Description |
|---|---|
| `JSONOutputParser` | Extract JSON from text |
| `PydanticOutputParser` | Parse to Pydantic model |
| `ListOutputParser` | Extract numbered lists |
| `MarkdownOutputParser` | Split by headings |

---

## ReAct Engine

```python
class ReActEngine:
    def __init__(
        self,
        llm: Any,
        tools: Optional[List[Any]] = None,
        max_iterations: int = 15,
        verbose: bool = False,
    )
    def run(
        self,
        system_prompt: str,
        user_prompt: str,
        context: Optional[str] = None,
        state: Optional[AgentState] = None,
    ) -> LLMResponse
```

---

## Exceptions

| Exception | Description |
|---|---|
| `MangabaError` | Base exception |
| `AgentError` | Agent execution error |
| `TaskError` | Task execution error |
| `CrewError` | Crew orchestration error |
| `LLMError` | LLM provider error |
| `AuthenticationError` | Invalid API key |
| `RateLimitError` | Rate limit exceeded |
| `RetryableError` | Retryable LLM error |
| `ContentFilterError` | Content filtered |
| `MaxIterationsError` | ReAct loop exceeded |
| `ToolError` | Tool execution error |
| `ToolNotFoundError` | Tool not found |
