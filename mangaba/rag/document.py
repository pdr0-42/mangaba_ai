"""
Document model for Mangaba AI RAG pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A chunk of content with associated metadata."""

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = Field(default=None, exclude=True)

    @property
    def page_content(self) -> str:
        """Alias kept for LangChain-style compatibility."""
        return self.content

    def __str__(self) -> str:
        return self.content[:120]
