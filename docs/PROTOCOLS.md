# 🔗 Protocols (A2A & MCP)

Protocolos de comunicação entre agents e integração com sistemas externos.

---

## A2A Protocol (Agent-to-Agent)

Protocolo para comunicação entre agents independentes.

### Modelos

| Modelo | Descrição |
|---|---|
| `Task` | Unidade de trabalho com ID, status, inputs/outputs |
| `Message` | Mensagem entre agents com conteúdo e metadata |
| `Artifact` | Resultado produzido por uma task |
| `TaskStatus` | Estado atual da task (pending, working, completed, failed) |

### Server

```python
from protocols.a2a import A2AServer

server = A2AServer(
    agent_name="ResearchAgent",
    host="localhost",
    port=8080,
)

# Registrar handler
@server.on_task
def handle_task(task):
    # Processar task
    return {
        "status": "completed",
        "result": "Research findings...",
    }

server.start()
```

### Client

```python
from protocols.a2a import A2AClient

client = A2AClient(server_url="http://localhost:8080")

# Enviar task
response = client.send_task(
    task_id="task_001",
    description="Research AI trends",
)

# Ver status
status = client.get_task_status("task_001")

# Streaming
for chunk in client.stream_task("task_001"):
    print(chunk)
```

---

## MCP Protocol (Model Context Protocol)

Protocolo para integração de tools e resources com LLMs.

### Server

```python
from protocols.mcp import MCPServer

server = MCPServer(name="MyTools")

# Registrar tool
@server.tool(name="calculator", description="Evaluate math expressions")
def calculator(expression: str) -> str:
    return str(eval(expression))

# Registrar resource
@server.resource(uri="file://docs/readme.md")
def readme() -> str:
    return open("README.md").read()

server.run(transport="stdio")
```

### Client

```python
from protocols.mcp import MCPClient

client = MCPClient()

# Conectar
client.connect("stdio")

# Listar tools
tools = client.list_tools()

# Executar tool
result = client.call_tool("calculator", {"expression": "2 + 2"})

# Ler resource
content = client.read_resource("file://docs/readme.md")

client.disconnect()
```

---

## Integração com Mangaba

### Agent via A2A

```python
from mangaba import Agent
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from protocols.a2a import A2AClient

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

# Agent que pode delegar via A2A
research_agent = Agent(
    role="Researcher",
    goal="Research topics via A2A protocol",
    backstory="Connected researcher",
    llm=llm,
)

# Client para outro agent
a2a_client = A2AClient(server_url="http://research-server:8080")
response = a2a_client.send_task(
    task_id="research_001",
    description="Research quantum computing advances",
)
```

### Tools via MCP

```python
from mangaba import Agent, BaseTool
from mangaba.core.types import LLMConfig
from mangaba.core.llm import create_llm_client
from protocols.mcp import MCPClient

llm_config = LLMConfig(provider="google", api_key="KEY", model="gemini-2.5-flash")
llm = create_llm_client(
    provider=llm_config.provider,
    api_key=llm_config.api_key,
    model=llm_config.model,
    temperature=llm_config.temperature,
    max_output_tokens=llm_config.max_tokens,
)

class MCPTool(BaseTool):
    """Tool que executa via MCP."""

    def __init__(self, mcp_client, tool_name):
        self.mcp_client = mcp_client
        self.tool_name = tool_name
        self.name = tool_name
        self.description = f"MCP tool: {tool_name}"

    def _run(self, **kwargs):
        return self.mcp_client.call_tool(self.tool_name, kwargs)

# Conectar ao MCP server
mcp = MCPClient()
mcp.connect("stdio")

# Criar tools do MCP
tools = [MCPTool(mcp, t.name) for t in mcp.list_tools()]

agent = Agent(
    role="MCP Agent",
    goal="Use MCP tools",
    backstory="Connected agent",
    tools=tools,
    llm=llm,
)
```
