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
    """Abstract base class for grouping related tools together.

    A Toolkit bundles related tools so they can be attached to an agent
    as a single unit.
    """

    @abstractmethod
    def get_tools(self) -> List[BaseTool]:
        """Return the list of tools in this toolkit.

        Returns:
            List of BaseTool instances.
        """


class FileToolkit(BaseToolkit):
    """Toolkit containing file I/O tools.

    Includes tools for reading files, writing files, and listing directories.
    """

    def get_tools(self) -> List[BaseTool]:
        """Return the list of file I/O tools.

        Returns:
            List containing FileReaderTool, FileWriterTool, and DirectoryListTool.
        """
        return [FileReaderTool(), FileWriterTool(), DirectoryListTool()]


class WebToolkit(BaseToolkit):
    """Toolkit containing web search tools.

    Includes tools for searching the web using DuckDuckGo.
    """

    def get_tools(self) -> List[BaseTool]:
        """Return the list of web search tools.

        Returns:
            List containing DuckDuckGoSearchTool.
        """
        return [DuckDuckGoSearchTool()]
