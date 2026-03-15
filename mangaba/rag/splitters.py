"""
Text splitters for Mangaba AI RAG pipeline.
"""

from __future__ import annotations

from typing import List

from mangaba.rag.document import Document


class RecursiveTextSplitter:
    """Split text recursively using a hierarchy of separators.

    Tries the first separator; if any chunk is still too large, falls
    back to subsequent separators.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] | None = None,
    ) -> None:
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_documents(self, documents: List[Document]) -> List[Document]:
        result: List[Document] = []
        for doc in documents:
            chunks = self._split(doc.content, self.separators)
            for i, chunk in enumerate(chunks):
                meta = {**doc.metadata, "chunk_index": i, "total_chunks": len(chunks)}
                result.append(Document(content=chunk, metadata=meta))
        return result

    def split_text(self, text: str) -> List[str]:
        return self._split(text, self.separators)

    def _split(self, text: str, separators: List[str]) -> List[str]:
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []

        sep = separators[0] if separators else ""
        remaining = separators[1:] if len(separators) > 1 else [""]

        parts = text.split(sep) if sep else list(text)

        chunks: List[str] = []
        current = ""
        for part in parts:
            joiner = sep if current else ""
            candidate = current + joiner + part
            if len(candidate) <= self.chunk_size:
                current = candidate
            else:
                if current.strip():
                    if len(current) > self.chunk_size:
                        chunks.extend(self._split(current, remaining))
                    else:
                        chunks.append(current.strip())
                current = part

        if current.strip():
            if len(current) > self.chunk_size:
                chunks.extend(self._split(current, remaining))
            else:
                chunks.append(current.strip())

        # Apply overlap
        if self.chunk_overlap > 0 and len(chunks) > 1:
            overlapped: List[str] = [chunks[0]]
            for i in range(1, len(chunks)):
                prev = chunks[i - 1]
                overlap_text = prev[-self.chunk_overlap:] if len(prev) > self.chunk_overlap else prev
                combined = overlap_text + chunks[i]
                overlapped.append(combined)
            return overlapped

        return chunks
