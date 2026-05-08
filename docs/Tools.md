# 🔧 Tools

O sistema de tools permite que agents executem ações externas via function calling.

---

## BaseTool

Toda tool herda de `BaseTool`:

```python
from mangaba import BaseTool
from pydantic import BaseModel

class SearchInput(BaseModel):
    query: str
    max_results: int = 5

class SearchTool(BaseTool):
    name = "web_search"
    description = "Search the web for current information"
    args_schema = SearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        # Implementação da busca
        results = search_web(query, limit=max_results)
        return "\n".join(f"- {r.title}: {r.snippet}" for r in results)
```

### Atributos da Classe

| Atributo | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `name` | `str` | ✅ | Nome único da tool |
| `description` | `str` | ✅ | Descrição para o LLM |
| `args_schema` | `BaseModel` | ❌ | Schema Pydantic para inputs |
| `return_direct` | `bool` | ❌ | Se True, retorna direto sem continuar loop ReAct |

### Métodos

| Método | Descrição |
|---|---|
| `_run(**kwargs) → Any` | Implementação da tool (obrigatório) |
| `run(**kwargs) → Any` | Executa com validação (herdado) |
| `get_function_schema() → dict` | Retorna schema JSON para function calling |

---

## @tool Decorator

Forma rápida de criar tools:

```python
from mangaba import tool

@tool
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression safely."""
    return str(eval(expression, {"__builtins__": {}}, {}))

# Uso
result = calculator.run(expression="2 + 2 * 3")
```

---

## Built-in Tools

### CalculatorTool

```python
from mangaba.tools.math_tools import CalculatorTool

calc = CalculatorTool()
result = calc.run(expression="15 * 25 + 100")
# "475"
```

### TextSplitterTool

```python
from mangaba.tools.text_tools import TextSplitterTool

splitter = TextSplitterTool()
chunks = splitter.run(text="Long text here...", chunk_size=100, overlap=20)
```

### WordCounterTool

```python
from mangaba.tools.text_tools import WordCounterTool

counter = WordCounterTool()
result = counter.run(text="Hello world this is a test")
# "23 words, 5 sentences"
```

---

## Toolkits

Coleções de tools relacionadas:

```python
from mangaba.tools.toolkit import BaseToolkit, FileToolkit, WebToolkit

# File toolkit
file_tools = FileToolkit()
print(file_tools.tools)  # [ReadFileTool, WriteFileTool, ...]

# Web toolkit
web_tools = WebToolkit()
print(web_tools.tools)   # [SearchTool, WebScraperTool, ...]

# Custom toolkit
class MyToolkit(BaseToolkit):
    @property
    def tools(self):
        return [CalculatorTool(), MyCustomTool()]
```

---

## Tools com Agents

```python
from mangaba import Agent
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

agent = Agent(
    role="Math Expert",
    goal="Solve complex calculations",
    backstory="Expert mathematician",
    tools=[CalculatorTool()],
    llm=llm,
)

# O agent usa a tool automaticamente via ReAct
result = agent.execute_task("What is 15% of 250? Add 100 to the result.")
```

---

## Schema de Função

Cada tool gera automaticamente um schema JSON para function calling:

```python
tool = CalculatorTool()
schema = tool.get_function_schema()
# {
#     "name": "calculator",
#     "description": "Evaluate mathematical expressions",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "expression": {"type": "string"}
#         },
#         "required": ["expression"]
#     }
# }
```

---

## return_direct

Quando `return_direct=True`, o agent para o loop ReAct após executar a tool:

```python
class FinalAnswerTool(BaseTool):
    name = "final_answer"
    description = "Return the final answer"
    return_direct = True  # Para o ReAct loop

    def _run(self, answer: str) -> str:
        return answer
```
