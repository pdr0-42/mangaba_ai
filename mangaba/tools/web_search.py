"""
Web search tool using multiple search engines
"""

import os
import requests
from typing import Optional, Dict, Any
from mangaba.tools.base import BaseTool


class SerperSearchTool(BaseTool):
    """
    Ferramenta de busca web usando Serper API.
    
    Requer: SERPER_API_KEY como variável de ambiente
    
    Exemplo:
        tool = SerperSearchTool()
        results = tool.run("latest AI trends 2024")
    """
    
    name = "serper_search"
    description = "Search the web using Serper API for current information and news"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self.api_key:
            raise ValueError("SERPER_API_KEY not found in environment variables")
        
        self.endpoint = "https://google.serper.dev/search"
    
    def _run(self, query: str, num_results: int = 10) -> str:
        """
        Realiza busca web e retorna resultados formatados.
        
        Args:
            query: Termo de busca
            num_results: Número de resultados (padrão: 10)
        
        Returns:
            String formatada com os resultados
        """
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "q": query,
            "num": num_results
        }
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Formata resultados
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
    """
    Ferramenta de busca web usando DuckDuckGo (sem necessidade de API key).
    
    Exemplo:
        tool = DuckDuckGoSearchTool()
        results = tool.run("Python programming tips")
    """
    
    name = "duckduckgo_search"
    description = "Search the web using DuckDuckGo (no API key required)"
    
    def _run(self, query: str, max_results: int = 5) -> str:
        """
        Realiza busca usando DuckDuckGo.
        """
        try:
            # Tenta importar duckduckgo_search
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
