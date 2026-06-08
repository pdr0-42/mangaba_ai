"""
Web search tool using multiple search engines
"""

import os
import requests
from typing import Optional
from mangaba.tools.base import BaseTool


class SerperSearchTool(BaseTool):
    """Web search tool using Serper API.

    Requires: SERPER_API_KEY as an environment variable.

    Example:
        tool = SerperSearchTool()
        results = tool.run("latest AI trends 2024")
    """

    name = "serper_search"
    description = "Search the web using Serper API for current information and news"

    def __init__(self, api_key: Optional[str] = None):
        """Initialize the Serper search tool.

        Args:
            api_key: Optional API key for Serper. If not provided,
                looks for SERPER_API_KEY environment variable.

        Raises:
            ValueError: If no API key is found.
        """
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")

        self.endpoint = "https://google.serper.dev/search"

    def _run(self, query: str, num_results: int = 10) -> str:
        """Perform a web search and return formatted results.

        Args:
            query: Search query.
            num_results: Number of results to return (default: 10).

        Returns:
            Formatted string with the search results.
        """
        headers = {"X-API-KEY": self.api_key, "Content-Type": "application/json"}

        payload = {"q": query, "num": num_results}

        try:
            response = requests.post(
                self.endpoint, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Format results
            results = []

            # Organic results
            if "organic" in data:
                for i, result in enumerate(data["organic"][:num_results], 1):
                    title = result.get("title", "No title")
                    link = result.get("link", "")
                    snippet = result.get("snippet", "")

                    results.append(f"{i}. {title}\n   {snippet}\n   URL: {link}")

            if not results:
                return "No results found."

            return "\n\n".join(results)

        except requests.exceptions.RequestException as e:
            return f"Error searching web: {str(e)}"
        except Exception as e:
            return f"Unexpected error: {str(e)}"


class DuckDuckGoSearchTool(BaseTool):
    """Web search tool using DuckDuckGo (no API key required).

    Example:
        tool = DuckDuckGoSearchTool()
        results = tool.run("Python programming tips")
    """

    name = "duckduckgo_search"
    description = "Search the web using DuckDuckGo (no API key required)"

    def _run(self, query: str, max_results: int = 5) -> str:
        """Perform a search using DuckDuckGo.

        Args:
            query: Search query.
            max_results: Maximum number of results to return (default: 5).

        Returns:
            Formatted string with the search results.
        """
        try:
            # Try to import duckduckgo_search
            try:
                from duckduckgo_search import DDGS
            except ImportError:
                return "Error: duckduckgo-search package not installed. Run: pip install duckduckgo-search"

            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return "No results found."

            formatted = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                body = result.get("body", "")
                link = result.get("href", "")

                formatted.append(f"{i}. {title}\n   {body}\n   URL: {link}")

            return "\n\n".join(formatted)

        except Exception as e:
            return f"Error searching with DuckDuckGo: {str(e)}"
