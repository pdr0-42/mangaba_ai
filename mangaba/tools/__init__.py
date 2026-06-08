"""Tools for Mangaba AI agents v3.0.

This module provides the tool system for agents, including:
- BaseTool: Abstract base class for creating custom tools
- @tool decorator: Convert functions into tools automatically
- BaseToolkit: Collection of related tools
- Built-in tools: Calculator, text processing, file I/O, web search

Example::

    from mangaba.tools import tool

    @tool
    def my_function(x: int) -> str:
        \"\"\"Do something with x.\"\"\"
        return str(x)
"""

from mangaba.tools.base import BaseTool
from mangaba.tools.decorator import tool
from mangaba.tools.toolkit import BaseToolkit, FileToolkit, WebToolkit
from mangaba.tools.math_tools import CalculatorTool
from mangaba.tools.text_tools import TextSplitterTool, WordCounterTool

__all__ = [
    "BaseTool",
    "tool",
    "BaseToolkit",
    "FileToolkit",
    "WebToolkit",
    "CalculatorTool",
    "TextSplitterTool",
    "WordCounterTool",
]
