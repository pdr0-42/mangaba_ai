"""
Toolkit grouping for Mangaba AI v3.0

A Toolkit bundles related tools together so they can be attached to an
agent as a single unit.

Example::

    kit = FileToolkit()
    agent = Agent(role="...", tools=kit.get_tools(), ...)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List

from mangaba.tools.base import BaseTool
from mangaba.tools.file_tools import FileReaderTool, FileWriterTool, DirectoryListTool
from mangaba.tools.web_search import DuckDuckGoSearchTool


class BaseToolkit(ABC):
    """Abstract grouping of related tools."""

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        ...


class FileToolkit(BaseToolkit):
    """File I/O tools: read, write, list directories."""

    def get_tools(self) -> List[BaseTool]:
        return [FileReaderTool(), FileWriterTool(), DirectoryListTool()]


class WebToolkit(BaseToolkit):
    """Web search tools."""

    def get_tools(self) -> List[BaseTool]:
        return [DuckDuckGoSearchTool()]
