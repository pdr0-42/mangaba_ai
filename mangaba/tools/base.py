"""
Base Tool class for agent tools
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class BaseTool(ABC):
    """
    Classe base para ferramentas que podem ser usadas por agentes.
    
    Exemplo:
        class WebSearchTool(BaseTool):
            name = "web_search"
            description = "Search the web for information"
            
            def _run(self, query: str) -> str:
                # Implementação da busca
                return search_results
    """
    
    name: str = "base_tool"
    description: str = "Base tool class"
    
    def run(self, *args, **kwargs) -> Any:
        """
        Executa a ferramenta com validação.
        """
        try:
            return self._run(*args, **kwargs)
        except Exception as e:
            return f"Error executing {self.name}: {str(e)}"
    
    @abstractmethod
    def _run(self, *args, **kwargs) -> Any:
        """
        Implementação específica da ferramenta.
        Deve ser sobrescrita pelas subclasses.
        """
        raise NotImplementedError("Tool must implement _run method")
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name='{self.name}')"
