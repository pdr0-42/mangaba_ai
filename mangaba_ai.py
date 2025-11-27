"""Mangaba AI

Um pacote Python para criação de agentes de IA inteligentes e versáteis.
"""

__version__ = "2.0.1"
__author__ = "Mangaba AI Team"
__email__ = "contato@mangaba.ai"
__description__ = "Agente de IA inteligente e versátil"

from mangaba_agent import MangabaAgent
from config import config, Config

__all__ = [
    "MangabaAgent",
    "config",
    "Config",
]
