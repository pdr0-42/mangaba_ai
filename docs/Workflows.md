# ⚡ Workflows

Pipeline engine para composição de tarefas com stages sequenciais, paralelos e condicionais.

---

## Pipeline

Executa uma sequência de stages, passando contexto entre eles:

```python
from mangaba import Pipeline, Stage
from mangaba.core.task import Task

pipeline = Pipeline(
    stages=[
        Stage("research", [research_task]),
        Stage("analysis", [analysis_task]),
        Stage("report", [report_task]),
    ],
    name="research_pipeline",
)

result = pipeline.run({"topic": "AI trends"})
print(result.final_output)
```

---

## Stage

Grupo nomeado de tasks dentro de um pipeline:

```python
from mangaba import Stage

stage = Stage(
    name="research",
    tasks=[task1, task2, task3],
)

# Executar
result = stage.run({"topic": "AI"})
print(result.stage_name)    # "research"
print(result.outputs)       # List[TaskOutput]
print(result.duration)      # Float (segundos)
```

---

## ParallelStage

Executa tasks concorrentemente via asyncio:

```python
from mangaba import ParallelStage

parallel = ParallelStage(
    name="parallel_analysis",
    tasks=[
        financial_task,
        technical_task,
        market_task,
    ],
)

result = parallel.run({"company": "Apple"})
# As tasks executam em paralelo
```

---

## ConditionalStage

Seleciona um branch baseado em condição runtime:

```python
from mangaba import ConditionalStage

def needs_deep_analysis(inputs):
    return inputs.get("complexity", "low") == "high"

conditional = ConditionalStage(
    name="analysis_router",
    condition=needs_deep_analysis,
    if_true=Stage("deep_analysis", [deep_task1, deep_task2]),
    if_false=Stage("quick_analysis", [quick_task]),
)

# Executa deep ou quick baseado na condição
result = conditional.run({"complexity": "high"})
```

---

## PipelineResult

```python
result = pipeline.run({"topic": "AI"})

result.stages         # List[StageResult]
result.duration       # Tempo total (segundos)
result.final_output   # Output do último stage com results
```

### StageResult

```python
stage_result = result.stages[0]
stage_result.stage_name   # Nome do stage
stage_result.outputs      # List[TaskOutput]
stage_result.duration     # Tempo do stage
```

---

## Exemplo Completo

```python
from mangaba import Agent, Task, Pipeline, Stage, ParallelStage, ConditionalStage
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
researcher = Agent(role="Researcher", goal="...", backstory="...", llm=llm)
analyst = Agent(role="Analyst", goal="...", backstory="..., llm=llm)
writer = Agent(role="Writer", goal="...", backstory="...", llm=llm)

# Tasks
research_task = Task(description="Research {topic}", expected_output="...", agent=researcher)
financial_task = Task(description="Financial analysis", expected_output="...", agent=analyst)
technical_task = Task(description="Technical analysis", expected_output="...", agent=analyst)
synthesis_task = Task(description="Synthesize findings", expected_output="...", agent=writer)
report_task = Task(description="Write final report", expected_output="...", agent=writer)

# Pipeline
pipeline = Pipeline(
    stages=[
        Stage("research", [research_task]),
        ParallelStage("parallel_analysis", [financial_task, technical_task]),
        Stage("synthesis", [synthesis_task]),
        Stage("report", [report_task]),
    ],
    name="report_pipeline",
)

result = pipeline.run({"topic": "AI market 2026"})

for stage in result.stages:
    print(f"{stage.stage_name}: {len(stage.outputs)} tasks ({stage.duration:.2f}s)")

print(f"\nFinal: {result.final_output[:200]}...")
```
