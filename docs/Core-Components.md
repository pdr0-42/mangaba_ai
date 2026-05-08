# 🧩 Core Components

Documentação dos componentes centrais do Mangaba AI: Agent, Task e Crew.

---

## Agent

O `Agent` é a unidade fundamental de inteligência. Cada agent possui:

- **Role** — Papel/função do agent
- **Goal** — Objetivo principal
- **Backstory** — Contexto/background
- **Tools** — Ferramentas disponíveis
- **Memory** — Sistema de memória
- **ReAct Engine** — Loop de raciocínio Thought → Action → Observation

### Criação

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client

# Configuração via LLMConfig
llm_config = LLMConfig(
    provider="google",
    model="gemini-2.5-flash",
    api_key="sua-api-key",
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
    role="Senior Data Analyst",
    goal="Analyze market trends and provide actionable insights",
    backstory="Expert in financial markets with 15 years of experience in quantitative analysis",
    llm=llm,                          # LLMClient instance
    tools=[],                         # List[BaseTool]
    verbose=False,                    # Log detalhado
    max_iterations=15,                # Máximo de iterações ReAct
    max_retry_on_error=3,             # Retries em caso de erro
    allow_delegation=True,            # Permitir delegação
    memory=None,                      # BaseMemory instance
    memory_config=None,               # MemoryConfig
    guardrails=[],                    # List[BaseGuardrail]
    output_parser=None,               # BaseOutputParser
    step_callback=None,               # Callback por step
)
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `role` | `str` | *required* | Papel do agent |
| `goal` | `str` | *required* | Objetivo principal |
| `backstory` | `str` | *required* | Contexto/background |
| `llm` | `LLMClient` | `None` | Cliente LLM ou string provider |
| `tools` | `List[BaseTool]` | `[]` | Ferramentas disponíveis |
| `verbose` | `bool` | `False` | Log detalhado |
| `max_iterations` | `int` | `15` | Máximo iterações ReAct |
| `max_retry_on_error` | `int` | `3` | Retries em erro |
| `allow_delegation` | `bool` | `True` | Delegar tasks a peers |
| `memory` | `BaseMemory` | `None` | Sistema de memória |
| `guardrails` | `List[BaseGuardrail]` | `[]` | Validadores de output |
| `output_parser` | `BaseOutputParser` | `None` | Parser de output |

### Métodos

| Método | Descrição |
|---|---|
| `execute_task(task: str, context: str?) → str` | Executa uma task via loop ReAct |
| `connect_to(other: Agent) → None` | Conecta a outro agent para delegação |
| `delegate(peer_id: str, task: str, context: str?) → str` | Delega task a peer |

### Exemplo

```python
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

agent = Agent(
    role="Researcher",
    goal="Find accurate information",
    backstory="Expert researcher",
    llm=llm,
)

result = agent.execute_task("What are the top 3 AI trends for 2026?")
print(result)
```

---

## Task

Uma `Task` é uma unidade de trabalho atribuída a um Agent.

### Criação

```python
from mangaba import Task

task = Task(
    description="Research {topic} and produce a report",
    expected_output="A detailed markdown report with findings",
    agent=researcher,               # Agent instance
    context=[],                     # List[Task] — dependências
    tools=[],                       # Tools extras para esta task
    output_file="output/report.md", # Salvar em arquivo
    callback=None,                  # Callback ao completar
    async_execution=False,          # Execução assíncrona
    human_input=False,              # Requer input humano
    guardrails=[],                  # Guardrails específicos
    output_parser=None,             # Parser específico
    retry_on_failure=0,             # Retries
)
```

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `description` | `str` | *required* | Descrição da task (suporta templates `{var}`) |
| `expected_output` | `str` | *required* | Descrição do output esperado |
| `agent` | `Agent` | *required* | Agent responsável |
| `context` | `List[Task]` | `[]` | Tasks anteriores cujo output é contexto |
| `output_file` | `str` | `None` | Path para salvar output |
| `callback` | `Callable` | `None` | Callback ao completar |
| `async_execution` | `bool` | `False` | Execução assíncrona |
| `human_input` | `bool` | `False` | Requer input humano |
| `retry_on_failure` | `int` | `0` | Número de retries |

### Métodos

| Método | Descrição |
|---|---|
| `execute(inputs: dict?) → TaskOutput` | Executa task sincronamente |
| `aexecute(inputs: dict?) → TaskOutput` | Executa task assincronamente |

### TaskOutput

```python
output = task.execute({"topic": "AI trends"})
print(output.result)         # Resultado em texto
print(output.description)    # Descrição da task
print(output.agent)          # Nome do agent
print(output.success)        # bool — sucesso?
print(output.timestamp)      # ISO timestamp
```

### Templates

Tasks suportam substituição de variáveis:

```python
task = Task(
    description="Write a report about {topic} for {audience}",
    expected_output="Report in markdown",
    agent=writer,
)

# As variáveis são substituídas ao executar
output = task.execute({"topic": "AI", "audience": "developers"})
# → "Write a report about AI for developers"
```

---

## Crew

`Crew` orquestra múltiplos agents trabalhando em múltiplas tasks.

### Criação

```python
from mangaba import Crew, Process

crew = Crew(
    agents=[researcher, analyst, writer],
    tasks=[research_task, analyze_task, write_task],
    process=Process.SEQUENTIAL,     # Modo de execução
    verbose=True,
)
```

### Modos de Processo

| Modo | Descrição |
|---|---|
| `Process.SEQUENTIAL` | Tasks executam uma após outra, em ordem |
| `Process.HIERARCHICAL` | Manager agent delega e revisa tasks dos workers |
| `Process.PARALLEL` | Tasks independentes executam concorrentemente (asyncio) |
| `Process.CONSENSUAL` | Todos os agents executam cada task; resultados são sintetizados |

### Parâmetros

| Parâmetro | Tipo | Default | Descrição |
|---|---|---|---|
| `agents` | `List[Agent]` | *required* | Agents da crew |
| `tasks` | `List[Task]` | *required* | Tasks a executar |
| `process` | `Process` | `SEQUENTIAL` | Modo de execução |
| `verbose` | `bool` | `False` | Log detalhado |
| `max_rpm` | `int` | `None` | Máximo requests/minuto |
| `memory` | `Any` | `None` | Memória compartilhada |

### Métodos

| Método | Descrição |
|---|---|
| `kickoff(inputs: dict?) → CrewOutput` | Executa a crew e retorna resultado |

### CrewOutput

```python
result = crew.kickoff({"topic": "AI"})
print(result.final_output)     # Output da última task
print(result.tasks_outputs)    # List[TaskOutput]
print(result.process)          # Process enum
print(result.duration)         # Tempo em segundos
print(result.crew_id)          # ID único
print(result.timestamp)        # ISO timestamp
```

### Exemplo Hierarchical

```python
crew = Crew(
    agents=[manager, researcher1, researcher2, writer],
    tasks=[research1, research2, write_report],
    process=Process.HIERARCHICAL,  # Manager delega e revisa
    verbose=True,
)
result = crew.kickoff()
```

### Exemplo Consensual

```python
crew = Crew(
    agents=[expert1, expert2, expert3],
    tasks=[analysis_task],
    process=Process.CONSENSUAL,    # Todos opinam, consensus é gerado
    verbose=True,
)
result = crew.kickoff()
```

### Exemplo Parallel

```python
crew = Crew(
    agents=[agent1, agent2, agent3],
    tasks=[independent_task1, independent_task2, independent_task3],
    process=Process.PARALLEL,      # Executa concorrentemente
    verbose=True,
)
result = crew.kickoff()
```

---

## Task Dependencies

Tasks podem depender de outras tasks via `context`:

```python
research = Task(
    description="Research AI trends",
    expected_output="List of trends",
    agent=researcher,
)

analysis = Task(
    description="Analyze the research findings",
    expected_output="Analysis report",
    agent=analyst,
    context=[research],  # Recebe output de research como contexto
)

# O output de research é automaticamente injetado no prompt de analysis
```

---

## Agent Delegation

Agents podem delegar tasks entre si:

```python
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

manager = Agent(role="Manager", goal="...", backstory="...", llm=llm)
worker = Agent(role="Worker", goal="...", backstory="...", llm=llm)

# Conectar agents
manager.connect_to(worker)

# Delegar
result = manager.delegate(worker.agent_id, "Research this topic")
```

> **Nota:** O `Crew` conecta automaticamente todos os agents entre si.
