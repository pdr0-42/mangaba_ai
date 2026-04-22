"""Mangaba AI v3.0 — Professional multi-agent orchestration framework."""

from mangaba.core.agent import Agent
from mangaba.core.task import Task
from mangaba.core.crew import Crew, Process
from mangaba.core.workflow import Pipeline, Stage, ParallelStage, ConditionalStage
from mangaba.core.events import EventBus, Event, EventType
from mangaba.core.exceptions import MangabaError
from mangaba.core.reasoning import ReActEngine
from mangaba.core.guardrails import GuardrailChain
from mangaba.core.output_parsers import JSONOutputParser, PydanticOutputParser
from mangaba.core.llm import LLMClient, create_llm_client, list_huggingface_models, hf_model_supports_tools, HF_OPEN_MODELS
from mangaba.tools.base import BaseTool
from mangaba.tools.decorator import tool

__version__ = "3.1.1"
__all__ = [
    # Core
    "Agent",
    "Task",
    "Crew",
    "Process",
    # Workflow
    "Pipeline",
    "Stage",
    "ParallelStage",
    "ConditionalStage",
    # LLM
    "LLMClient",
    "create_llm_client",
    "list_huggingface_models",
    "hf_model_supports_tools",
    "HF_OPEN_MODELS",
    # Events
    "EventBus",
    "Event",
    "EventType",
    # Reasoning
    "ReActEngine",
    # Guardrails & Parsers
    "GuardrailChain",
    "JSONOutputParser",
    "PydanticOutputParser",
    # Tools
    "BaseTool",
    "tool",
    # Exceptions
    "MangabaError",
]
