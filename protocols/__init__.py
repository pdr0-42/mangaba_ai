"""Protocolos A2A e MCP para Mangaba AI.

This module provides inter-agent communication protocols:

- A2A (Agent-to-Agent): Protocol for direct agent communication
  with message passing and agent discovery.

- MCP (Model Context Protocol): Protocol for context sharing
  and session management between agents and tools.

These protocols enable multi-agent systems where agents can
communicate, share context, and coordinate actions.
"""

from .a2a import A2AProtocol, A2AMessage, A2AAgent
from .mcp import MCPProtocol, MCPContext, MCPSession

__all__ = [
    "A2AProtocol",
    "A2AMessage",
    "A2AAgent",
    "MCPProtocol",
    "MCPContext",
    "MCPSession",
]
