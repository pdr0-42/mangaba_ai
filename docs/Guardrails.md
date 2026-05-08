# 🛡️ Guardrails & Output Parsers

Validação de entrada/saída e parsing de outputs estruturados.

---

## Guardrails

Guardrails validam e transformam o output do LLM antes de retornar ao usuário.

### BaseGuardrail

```python
from mangaba.core.guardrails import BaseGuardrail

class BaseGuardrail:
    def validate(self, text: str) -> str:
        """Valida texto. Retorna texto (possivelmente modificado) ou raise ValueError."""
```

### Built-in Guardrails

#### LengthGuardrail

```python
from mangaba.core.guardrails import LengthGuardrail

# Mínimo e máximo
guardrail = LengthGuardrail(min_length=100, max_length=5000)

text = guardrail.validate("Short text")  # Raises ValueError: too short
text = guardrail.validate("Very " * 2000)  # Trunca para 5000 chars
```

#### ContentFilterGuardrail

```python
from mangaba.core.guardrails import ContentFilterGuardrail

# Padrões bloqueados (default: passwords, secrets, API keys)
guardrail = ContentFilterGuardrail()

# Custom patterns
guardrail = ContentFilterGuardrail(
    blocked_patterns=[
        r'\bSSN\s*[:=]\s*\d{3}-\d{2}-\d{4}',
        r'\bcredit[_-]?card\s*\d{16}',
    ]
)

text = guardrail.validate("Password: secret123")
# "Password: [REDACTED]"
```

#### SchemaGuardrail

```python
from mangaba.core.guardrails import SchemaGuardrail
from pydantic import BaseModel

class ReportSchema(BaseModel):
    title: str
    findings: list[str]
    conclusion: str

guardrail = SchemaGuardrail(schema=ReportSchema)

text = guardrail.validate('{"title": "AI Report", "findings": ["..."], "conclusion": "..."}')
# Passa se o JSON corresponder ao schema
```

### GuardrailChain

```python
from mangaba.core.guardrails import GuardrailChain, LengthGuardrail, ContentFilterGuardrail

chain = GuardrailChain([
    LengthGuardrail(min_length=50, max_length=10000),
    ContentFilterGuardrail(),
])

result = chain.validate(raw_llm_output)
```

### Uso com Agent

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from mangaba.core.guardrails import LengthGuardrail, ContentFilterGuardrail

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

agent = Agent(
    role="Writer",
    goal="Write reports",
    backstory="Professional writer",
    guardrails=[
        LengthGuardrail(min_length=200),
        ContentFilterGuardrail(),
    ],
    llm=llm,
)
```

---

## Output Parsers

Parse raw LLM text em objetos Python estruturados.

### BaseOutputParser

```python
from mangaba.core.output_parsers import BaseOutputParser

class BaseOutputParser:
    def parse(self, text: str) -> Any: ...
    def get_format_instructions(self) -> str: ...
```

### JSONOutputParser

Extrai JSON do output do LLM:

```python
from mangaba.core.output_parsers import JSONOutputParser

parser = JSONOutputParser()

# JSON em code block
result = parser.parse('''
Here is the data:
```json
{"name": "John", "age": 30}
```
''')
# {"name": "John", "age": 30}

# JSON inline
result = parser.parse('Some text {"name": "John"} more text')
# {"name": "John"}
```

### PydanticOutputParser

Parse para modelo Pydantic:

```python
from mangaba.core.output_parsers import PydanticOutputParser
from pydantic import BaseModel

class Person(BaseModel):
    name: str
    age: int
    email: str

parser = PydanticOutputParser(model=Person)

# Instruções para o prompt
instructions = parser.get_format_instructions()
# "Respond with a JSON object matching this schema: ..."

# Parse
person = parser.parse('{"name": "John", "age": 30, "email": "john@example.com"}')
print(person.name)  # "John"
print(person.age)   # 30
```

### ListOutputParser

Extrai listas do texto:

```python
from mangaba.core.output_parsers import ListOutputParser

parser = ListOutputParser()

items = parser.parse("""
1. First item
2. Second item
3. Third item
""")
# ["First item", "Second item", "Third item"]
```

### MarkdownOutputParser

Split markdown por headings:

```python
from mangaba.core.output_parsers import MarkdownOutputParser

parser = MarkdownOutputParser()

sections = parser.parse("""
# Introduction
Some intro text

# Analysis
Analysis content

# Conclusion
Conclusion text
""")
# {
#     "Introduction": "Some intro text",
#     "Analysis": "Analysis content",
#     "Conclusion": "Conclusion text",
# }
```

### Uso com Task

```python
from mangaba import Task
from mangaba.core.output_parsers import JSONOutputParser

task = Task(
    description="Return analysis as JSON",
    expected_output="JSON with findings",
    agent=analyst,
    output_parser=JSONOutputParser(),
)
```
