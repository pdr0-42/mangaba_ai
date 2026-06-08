"""
Document model for Mangaba AI RAG pipeline.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """A chunk of content with associated metadata.

    This class represents a document or document chunk in the RAG pipeline,
    containing the text content, optional metadata, and optional embedding vector.

    Attributes:
        content: The text content of the document.
        metadata: Optional metadata dictionary associated with the document.
        embedding: Optional embedding vector for the document content.
    """

    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    embedding: Optional[List[float]] = Field(default=None, exclude=True)

    @property
    def page_content(self) -> str:
        """Alias for content, kept for LangChain-style compatibility.

        Returns:
            The document content.
        """
        return self.content

    def __str__(self) -> str:
        """Return a string representation of the document.

        Returns:
            The first 120 characters of the document content.
        """
        return self.content[:120]
