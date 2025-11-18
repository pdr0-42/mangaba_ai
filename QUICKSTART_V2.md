# 🎯 Mangaba AI 2.0 - Quick Start Guide

## 🆕 Novidades da Versão 2.0

Mangaba AI agora compete diretamente com CrewAI com funcionalidades enterprise-grade:

### ✨ Novas Funcionalidades

- **🤖 Agents com Roles/Goals/Backstory** - Agentes especializados e personalizados
- **📋 Tasks Estruturadas** - Sistema completo de orquestração de tarefas
- **👥 Crew Orchestration** - Coordenação de múltiplos agentes
- **🔧 Tools Ecosystem** - Ferramentas para web search, files, etc.
- **📊 Process Types** - Sequential e Hierarchical

---

## 🚀 Instalação

```bash
# Via pip
pip install mangaba>=2.0.0

# Via UV (recomendado)
uv pip install mangaba>=2.0.0
```

---

## 📖 Uso Básico

### 1️⃣ Agent Simples (Single Agent)

```python
from mangaba import Agent

# Criar agente especializado
agent = Agent(
    role="Senior Data Analyst",
    goal="Analyze data and provide insights",
    backstory="You are an expert in data analysis with 10 years experience",
    verbose=True
)

# Executar tarefa
result = agent.execute_task(
    task_description="Analyze the impact of AI on healthcare",
    context="Focus on recent developments in 2024-2025"
)

print(result)
```

### 2️⃣ Multiple Agents (Crew)

```python
from mangaba import Agent, Task, Crew, Process

# Definir agentes
researcher = Agent(
    role="Research Analyst",
    goal="Find and analyze information",
    backstory="Expert researcher with keen analytical skills"
)

writer = Agent(
    role="Content Writer",
    goal="Create engaging reports",
    backstory="Professional writer specialized in tech content"
)

# Definir tarefas
research = Task(
    description="Research AI trends in {year}",
    expected_output="List of 10 key trends with sources",
    agent=researcher
)

report = Task(
    description="Write a report about the findings",
    expected_output="Comprehensive report in markdown",
    agent=writer,
    context=[research],  # Depende da pesquisa
    output_file="report.md"
)

# Criar crew
crew = Crew(
    agents=[researcher, writer],
    tasks=[research, report],
    process=Process.SEQUENTIAL,
    verbose=True
)

# Executar
result = crew.kickoff(inputs={"year": "2025"})
print(result.final_output)
```

### 3️⃣ Hierarchical Process (com Gerente)

```python
from mangaba import Agent, Task, Crew, Process

# Manager (primeiro agente)
manager = Agent(
    role="Project Manager",
    goal="Coordinate team and ensure quality",
    backstory="Experienced manager with great leadership",
    allow_delegation=True
)

# Workers
developer = Agent(
    role="Software Developer",
    goal="Write clean, efficient code",
    backstory="Senior developer with expertise in Python"
)

tester = Agent(
    role="QA Engineer",
    goal="Ensure code quality",
    backstory="Detail-oriented QA with testing expertise"
)

# Tasks
dev_task = Task(
    description="Develop a user authentication system",
    expected_output="Working code with documentation",
    agent=developer
)

test_task = Task(
    description="Test the authentication system",
    expected_output="Test report with coverage",
    agent=tester,
    context=[dev_task]
)

# Hierarchical crew
crew = Crew(
    agents=[manager, developer, tester],  # Manager primeiro!
    tasks=[dev_task, test_task],
    process=Process.HIERARCHICAL,
    verbose=True
)

result = crew.kickoff()
```

---

## 🔧 Tools (Ferramentas)

### Web Search

```python
from mangaba import Agent
from mangaba.tools.web_search import DuckDuckGoSearchTool

agent = Agent(
    role="Research Assistant",
    goal="Find information online",
    backstory="Expert at online research",
    tools=[DuckDuckGoSearchTool()]
)
```

### File Operations

```python
from mangaba.tools.file_tools import FileReaderTool, FileWriterTool

reader = FileReaderTool()
writer = FileWriterTool()

# Ler arquivo
content = reader.run("document.txt")

# Escrever arquivo
writer.run("output.txt", "Content to save")
```

---

## 📊 Process Types

### Sequential
Tarefas executadas uma após a outra em ordem:
```python
crew = Crew(
    agents=[agent1, agent2],
    tasks=[task1, task2],
    process=Process.SEQUENTIAL
)
```

### Hierarchical
Primeiro agente atua como gerente, delegando para os outros:
```python
crew = Crew(
    agents=[manager, worker1, worker2],  # Manager primeiro!
    tasks=[task1, task2],
    process=Process.HIERARCHICAL
)
```

---

## 🎯 Exemplos Práticos

### Exemplo 1: Blog Post Generator

```python
from mangaba import Agent, Task, Crew, Process

# Agents
researcher = Agent(
    role="Content Researcher",
    goal="Research topics thoroughly",
    backstory="Expert at finding relevant information"
)

writer = Agent(
    role="Blog Writer",
    goal="Write engaging blog posts",
    backstory="Creative writer with SEO expertise"
)

editor = Agent(
    role="Editor",
    goal="Polish and improve content",
    backstory="Detail-oriented editor"
)

# Tasks
research = Task(
    description="Research about {topic}",
    expected_output="Key points and data",
    agent=researcher
)

write = Task(
    description="Write blog post about {topic}",
    expected_output="Complete blog post",
    agent=writer,
    context=[research]
)

edit = Task(
    description="Edit and improve the blog post",
    expected_output="Final polished version",
    agent=editor,
    context=[write],
    output_file="blog_post.md"
)

# Execute
crew = Crew(
    agents=[researcher, writer, editor],
    tasks=[research, write, edit],
    process=Process.SEQUENTIAL,
    verbose=True
)

result = crew.kickoff(inputs={"topic": "Future of AI"})
```

### Exemplo 2: Market Analysis Team

```python
from mangaba import Agent, Task, Crew, Process

# Manager + Team
manager = Agent(
    role="Analysis Team Lead",
    goal="Coordinate market analysis",
    backstory="Senior analyst with team leadership"
)

data_analyst = Agent(
    role="Data Analyst",
    goal="Analyze market data",
    backstory="Expert in data science"
)

report_writer = Agent(
    role="Report Writer",
    goal="Create professional reports",
    backstory="Business report specialist"
)

# Tasks
analysis = Task(
    description="Analyze {market} trends",
    expected_output="Data analysis with insights",
    agent=data_analyst
)

report = Task(
    description="Create executive report",
    expected_output="Professional report",
    agent=report_writer,
    context=[analysis]
)

# Hierarchical execution
crew = Crew(
    agents=[manager, data_analyst, report_writer],
    tasks=[analysis, report],
    process=Process.HIERARCHICAL,
    verbose=True
)

result = crew.kickoff(inputs={"market": "AI Technology"})
```

---

## 🔄 Migration from 1.x

### Antes (v1.x):
```python
from mangaba_ai import MangabaAgent

agent = MangabaAgent()
result = agent.chat("Hello")
```

### Agora (v2.0):
```python
from mangaba import Agent, Task

agent = Agent(
    role="Assistant",
    goal="Help users",
    backstory="Helpful AI assistant"
)

result = agent.execute_task("Greet the user")
```

---

## 📚 Mais Recursos

- **[Documentação Completa](docs/WIKI.md)**
- **[Exemplos Avançados](examples/crew_example.py)**
- **[API Reference](docs/API.md)**
- **[Roadmap](ROADMAP_CREWAI_COMPARISON.md)**

---

## 🆚 Mangaba vs CrewAI

| Feature | Mangaba AI 2.0 | CrewAI |
|---------|----------------|--------|
| Agents com Roles | ✅ | ✅ |
| Tasks Estruturadas | ✅ | ✅ |
| Crew Orchestration | ✅ | ✅ |
| Sequential Process | ✅ | ✅ |
| Hierarchical Process | ✅ | ✅ |
| MCP Protocol | ✅ | ❌ |
| A2A Protocol | ✅ | ❌ |
| Docs em PT-BR | ✅ | ❌ |
| UV Support | ✅ | ❌ |

---

## 🤝 Contribuindo

Contribuições são bem-vindas! Veja [CONTRIBUICAO.md](docs/CONTRIBUICAO.md)

---

## 📄 Licença

MIT License - veja [LICENSE](LICENSE)
