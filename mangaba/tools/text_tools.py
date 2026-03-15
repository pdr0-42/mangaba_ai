"""
Text processing tools for Mangaba AI v3.0
"""

from __future__ import annotations

import re
from typing import List

from pydantic import BaseModel, Field

from mangaba.tools.base import BaseTool


# ── Text Splitter ──────────────────────────────────────────────────────────

class TextSplitInput(BaseModel):
    text: str = Field(..., description="The text to split into chunks")
    chunk_size: int = Field(default=1000, description="Maximum characters per chunk")
    chunk_overlap: int = Field(default=200, description="Overlap between consecutive chunks")


class TextSplitterTool(BaseTool):
    """Split text into smaller overlapping chunks."""

    name = "text_splitter"
    description = "Split long text into smaller chunks with optional overlap"
    args_schema = TextSplitInput

    _SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

    def _run(self, text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> str:
        chunks = self._recursive_split(text, chunk_size, chunk_overlap, self._SEPARATORS)
        result_lines = [f"--- Chunk {i+1}/{len(chunks)} ---\n{c}" for i, c in enumerate(chunks)]
        return "\n\n".join(result_lines)

    def _recursive_split(
        self, text: str, chunk_size: int, overlap: int, separators: List[str]
    ) -> List[str]:
        if len(text) <= chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining_seps = separators[1:] if len(separators) > 1 else [""]
        parts = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        current = ""
        for part in parts:
            candidate = f"{current}{sep}{part}" if current else part
            if len(candidate) <= chunk_size:
                current = candidate
            else:
                if current:
                    if len(current) <= chunk_size:
                        chunks.append(current.strip())
                    else:
                        chunks.extend(self._recursive_split(current, chunk_size, overlap, remaining_seps))
                current = part

        if current.strip():
            if len(current) <= chunk_size:
                chunks.append(current.strip())
            else:
                chunks.extend(self._recursive_split(current, chunk_size, overlap, remaining_seps))

        # Apply overlap
        if overlap > 0 and len(chunks) > 1:
            overlapped: List[str] = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = chunks[i - 1]
                overlap_text = prev[-overlap:] if len(prev) > overlap else prev
                overlapped.append(overlap_text + chunks[i])
            return overlapped
        return chunks


# ── Word Counter ───────────────────────────────────────────────────────────

class WordCountInput(BaseModel):
    text: str = Field(..., description="Text to count words in")


class WordCounterTool(BaseTool):
    """Count words, sentences, and characters in text."""

    name = "word_counter"
    description = "Count words, sentences, and characters in text"
    args_schema = WordCountInput

    def _run(self, text: str) -> str:
        words = len(text.split())
        chars = len(text)
        sentences = len(re.split(r'[.!?]+', text.strip())) - 1 if text.strip() else 0
        paragraphs = len([p for p in text.split("\n\n") if p.strip()])
        return (
            f"Words: {words}\n"
            f"Characters: {chars}\n"
            f"Sentences: {max(sentences, 0)}\n"
            f"Paragraphs: {paragraphs}"
        )
