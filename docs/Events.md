# 📡 Events & Callbacks

Sistema de eventos para observabilidade, logging e integração com sistemas externos.

---

## EventType

Tipos de eventos emitidos pelo framework:

| Categoria | Eventos |
|---|---|
| **Agent** | `AGENT_START`, `AGENT_END`, `AGENT_ERROR` |
| **LLM** | `LLM_START`, `LLM_END`, `LLM_ERROR`, `LLM_RETRY`, `LLM_STREAM_CHUNK` |
| **Tools** | `TOOL_START`, `TOOL_END`, `TOOL_ERROR` |
| **ReAct** | `REACT_STEP`, `REACT_THOUGHT`, `REACT_ACTION`, `REACT_OBSERVATION` |
| **Task** | `TASK_START`, `TASK_END`, `TASK_ERROR` |
| **Crew** | `CREW_START`, `CREW_END`, `CREW_ERROR` |
| **Memory** | `MEMORY_ADD`, `MEMORY_SEARCH` |
| **Guardrails** | `GUARDRAIL_PASS`, `GUARDRAIL_FAIL` |
| **Generic** | `CUSTOM` |

---

## Event

Modelo de evento imutável:

```python
from mangaba.core.events import Event, EventType

event = Event(
    event_type=EventType.AGENT_START,
    source_id="agent_123",
    source_type="Agent",
    data={"role": "Researcher", "task": "Research AI trends"},
    trace_id="trace_abc",
)

print(event.event_type)   # EventType.AGENT_START
print(event.data)         # {"role": "Researcher", ...}
print(event.timestamp)    # ISO datetime string
```

---

## EventBus

Singleton global para publish/subscribe:

```python
from mangaba.core.events import EventBus, Event, EventType

# Registrar handler
def on_agent_start(event: Event):
    print(f"Agent started: {event.data.get('role')}")

EventBus.register(on_agent_start, event_types={EventType.AGENT_START})

# Emitir evento (feito automaticamente pelo framework)
EventBus.emit(Event(
    event_type=EventType.AGENT_START,
    source_id="agent_1",
    data={"role": "Researcher"},
))

# Desregistrar
EventBus.unregister(on_agent_start)

# Reset (limpa todos os handlers)
EventBus.reset()
```

---

## BaseCallback

Interface para handlers de eventos:

```python
from mangaba.core.events import BaseCallback, Event, EventType

class LoggingCallback(BaseCallback):
    # Opcional: filtrar tipos de evento
    event_filter = {
        EventType.AGENT_START,
        EventType.AGENT_END,
        EventType.TASK_START,
        EventType.TASK_END,
    }

    def on_event(self, event: Event) -> None:
        print(f"[{event.timestamp}] {event.event_type.value}")
        print(f"  Source: {event.source_id}")
        print(f"  Data: {event.data}")

# Registrar
callback = LoggingCallback()
EventBus.register(callback)
```

---

## CallbackManager

Gerencia coleção de callbacks:

```python
from mangaba.core.events import CallbackManager, BaseCallback, Event

manager = CallbackManager()
manager.add(callback1)
manager.add(callback2)
manager.emit(event)
manager.remove(callback1)
```

---

## Exemplo: Logger Completo

```python
from mangaba.core.events import EventBus, Event, EventType, BaseCallback

class VerboseCallback(BaseCallback):
    def on_event(self, event: Event) -> None:
        if event.event_type == EventType.AGENT_START:
            print(f"🚀 Agent: {event.data.get('role')}")
        elif event.event_type == EventType.AGENT_END:
            print(f"✅ Agent done: {event.data.get('result_preview', '')[:50]}...")
        elif event.event_type == EventType.TOOL_START:
            print(f"🔧 Tool: {event.data.get('tool')}")
        elif event.event_type == EventType.REACT_OBSERVATION:
            print(f"👁️ Observation: {event.data.get('observation_preview', '')[:100]}...")
        elif event.event_type == EventType.CREW_START:
            print(f"👥 Crew started: {event.data.get('agents')} agents, {event.data.get('tasks')} tasks")
        elif event.event_type == EventType.CREW_END:
            print(f"🏁 Crew finished in {event.data.get('duration', 0):.2f}s")

EventBus.register(VerboseCallback())

# Configurar agent com LLMConfig
from mangaba import Agent
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

agent = Agent(role="Researcher", goal="...", backstory="...", llm=llm)
agent.execute_task("Research AI trends")
```

---

## Exemplo: Tracing

```python
import json
from mangaba.core.events import EventBus, Event, EventType, BaseCallback

class TraceCallback(BaseCallback):
    def __init__(self, output_file: str):
        self.output_file = output_file
        self.traces = []

    def on_event(self, event: Event) -> None:
        self.traces.append({
            "type": event.event_type.value,
            "source": event.source_id,
            "data": event.data,
            "timestamp": event.timestamp,
        })

    def save(self):
        with open(self.output_file, "w") as f:
            json.dump(self.traces, f, indent=2)

tracer = TraceCallback("trace.json")
EventBus.register(tracer)

# ... executar agents/crews ...

tracer.save()  # Salva trace em JSON
```
