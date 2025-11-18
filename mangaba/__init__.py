"""
Mangaba AI - Framework de Agentes IA com Protocolos A2A e MCP

Multi-agent orchestration framework com suporte a roles, tasks e crews.
"""

from mangaba.core.agent import Agent
from mangaba.core.task import Task
from mangaba.core.crew import Crew, Process
from mangaba.tools.base import BaseTool

__version__ = "2.0.0"
__all__ = ["Agent", "Task", "Crew", "Process", "BaseTool"]
