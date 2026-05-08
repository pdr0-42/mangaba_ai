# 💡 Examples

Exemplos práticos de uso do Mangaba AI.

---

## Exemplos Básicos

### 1. Agente Simples

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

llm_config = LLMConfig(
    provider="google",
    api_key="KEY",
    model="gemini-2.5-flash",
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

agent = Agent(
    role="Professor",
    goal="Explicar conceitos de forma clara",
    backstory="Professor experiente com didática excepcional",
    llm=llm,
)

print(agent.execute_task("Explique o que é machine learning para um iniciante"))
```

### 2. Multi-Agent Crew

```python
from mangaba import Agent, Task, Crew, Process
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# Agents
researcher = Agent(
    role="Researcher", goal="Find data", backstory="Expert researcher", llm=llm,
)
writer = Agent(
    role="Writer", goal="Write reports", backstory="Professional writer", llm=llm,
)

# Tasks
research = Task(
    description="Research {topic} trends",
    expected_output="List of findings",
    agent=researcher,
)
report = Task(
    description="Write comprehensive report",
    expected_output="Markdown report",
    agent=writer,
    context=[research],
)

# Crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, report],
    process=Process.SEQUENTIAL,
)

result = crew.kickoff({"topic": "AI agents"})
print(result)
```

### 3. Agent com Tools

```python
from mangaba import Agent, BaseTool
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from mangaba.tools.math_tools import CalculatorTool

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

class WeatherTool(BaseTool):
    name = "weather"
    description = "Get current weather for a city"

    def _run(self, city: str) -> str:
        # Simulação
        return f"Weather in {city}: 25°C, Sunny"

agent = Agent(
    role="Travel Planner",
    goal="Plan trips based on weather",
    backstory="Expert travel agent",
    tools=[WeatherTool(), CalculatorTool()],
    llm=llm,
)

print(agent.execute_task("What's the weather in São Paulo and Tokyo?"))
```

### 4. RAG Pipeline

```python
from mangaba.rag import TextLoader, RecursiveTextSplitter, Retriever, RAGChain
from mangaba.embeddings import OpenAIEmbedding
from mangaba.vectorstores import InMemoryVectorStore
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# Load & split
loader = TextLoader("docs/knowledge.txt")
docs = loader.load()
splitter = RecursiveTextSplitter(chunk_size=500)
chunks = splitter.split_documents(docs)

# Setup
embedding = OpenAIEmbedding(api_key="KEY")
store = InMemoryVectorStore()
retriever = Retriever(embedding=embedding, store=store)
retriever.add_documents(chunks)

# RAG Chain
llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)
chain = RAGChain(llm=llm, retriever=retriever, top_k=3)

answer = chain.ask("How do I configure the system?")
print(answer)
```

### 5. Vector Store com Redis

```python
from mangaba.vectorstores import RedisVectorStore
from mangaba.embeddings import OpenAIEmbedding

embed = OpenAIEmbedding(api_key="KEY")
store = RedisVectorStore(
    url="redis://localhost:6379",
    index_name="my_docs",
    vector_dimensions=1536,
)

texts = ["Python tutorial", "JavaScript guide", "Rust fundamentals"]
embeddings = embed.embed_batch(texts)

ids = store.add(texts, embeddings, [{"lang": "python"}, {"lang": "js"}, {"lang": "rust"}])
results = store.search(embed.embed_text("programming language"), top_k=2)

for r in results:
    print(f"{r['content']} (score: {r['score']:.3f})")

store.close()
```

### 6. Vector Store com PostgreSQL

```python
from mangaba.vectorstores import PostgresVectorStore

store = PostgresVectorStore(
    url="postgresql://postgres:minhasenha@localhost:5432/mangaba",
    table_name="embeddings",
    vector_dimensions=1536,
)

store.add(texts, embeddings)
results = store.search(query_embedding, top_k=5)
store.close()
```

### 7. Workflow Pipeline

```python
from mangaba import Pipeline, Stage, ParallelStage, ConditionalStage

pipeline = Pipeline(stages=[
    Stage("research", [research_task]),
    ParallelStage("analysis", [financial_task, technical_task]),
    ConditionalStage("expand",
        condition=lambda inputs: inputs.get("deep", False),
        if_true=Stage("deep", [deep_analysis_task]),
        if_false=Stage("quick", [quick_analysis_task]),
    ),
    Stage("report", [report_task]),
])

result = pipeline.run({"topic": "AI", "deep": True})
for stage in result.stages:
    print(f"{stage.stage_name}: {stage.duration:.2f}s")
```

### 8. Guardrails & Output Parsers

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from mangaba.core.guardrails import LengthGuardrail, ContentFilterGuardrail
from mangaba.core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

class AnalysisSchema(BaseModel):
    title: str
    points: list[str]
    conclusion: str

parser = PydanticOutputParser(model=AnalysisSchema)

agent = Agent(
    role="Analyst",
    goal="Provide structured analysis",
    backstory="Expert analyst",
    guardrails=[
        LengthGuardrail(min_length=100),
        ContentFilterGuardrail(),
    ],
    output_parser=parser,
    llm=llm,
)

result = agent.execute_task("Analyze the AI market")
print(result)  # AnalysisSchema instance
```

### 9. Events & Observability

```python
from mangaba.core.events import EventBus, Event, EventType, BaseCallback
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

class Logger(BaseCallback):
    def on_event(self, event: Event) -> None:
        print(f"[{event.event_type.value}] {event.data}")

EventBus.register(Logger())

# Agora cada ação do agent emite eventos
agent = Agent(role="...", goal="...", backstory="...", llm=llm)
agent.execute_task("Do something")
# [agent_start] {...}
# [tool_start] {...}
# [react_observation] {...}
# [agent_end] {...}
```

### 10. @tool Decorator

```python
from mangaba import Agent, tool
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

@tool
def search(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    results = duckduckgo_search(query, limit=max_results)
    return "\n".join(f"- {r['title']}" for r in results)

@tool
def calculate(expression: str) -> str:
    """Evaluate a mathematical expression."""
    return str(eval(expression, {"__builtins__": {}}, {}))

agent = Agent(
    role="Researcher",
    goal="Research and calculate",
    backstory="Expert researcher",
    tools=[search, calculate],
    llm=llm,
)

result = agent.execute_task("Search for GDP of Brazil and calculate 10% of it")
```

---

## Exemplos Avançados

### Hierarchical Crew

```python
crew = Crew(
    agents=[manager, worker1, worker2, worker3],
    tasks=[task1, task2, task3],
    process=Process.HIERARCHICAL,  # Manager delega e revisa
)
result = crew.kickoff()
```

### Consensual Crew

```python
crew = Crew(
    agents=[expert1, expert2, expert3],
    tasks=[analysis_task],
    process=Process.CONSENSUAL,  # Todos opinam
)
result = crew.kickoff()
```

### Parallel Crew

```python
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[independent1, independent2, independent3],
    process=Process.PARALLEL,  # Concorrente
)
result = crew.kickoff()
```

### Memory Persistence

```python
from mangaba.memory import LongTermMemory
from mangaba.embeddings import OpenAIEmbedding
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

memory = LongTermMemory(
    db_path="./agent_memory.db",
    embedding=OpenAIEmbedding(api_key="KEY"),
    enable_vector_search=True,
)

agent = Agent(
    role="Assistant",
    goal="Remember context",
    backstory="Helpful assistant with memory",
    memory=memory,
    llm=llm,
)

# Memórias persistem entre execuções
agent.execute_task("My name is João and I like Python")
# ... reiniciar app ...
agent.execute_task("What is my name?")  # "João"
```
