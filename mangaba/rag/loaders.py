"""
Document loaders for Mangaba AI RAG pipeline.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Dict, List, Optional

from mangaba.rag.document import Document


class TextLoader:
    """Load a plain-text file as a single Document."""

    def __init__(self, file_path: str, encoding: str = "utf-8") -> None:
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        path = Path(self.file_path)
        text = path.read_text(encoding=self.encoding)
        return [Document(content=text, metadata={"source": str(path)})]


class CSVLoader:
    """Load a CSV file — each row becomes a Document."""

    def __init__(
        self,
        file_path: str,
        content_columns: Optional[List[str]] = None,
        encoding: str = "utf-8",
    ) -> None:
        self.file_path = file_path
        self.content_columns = content_columns
        self.encoding = encoding

    def load(self) -> List[Document]:
        path = Path(self.file_path)
        docs: List[Document] = []
        with path.open(encoding=self.encoding, newline="") as fh:
            reader = csv.DictReader(fh)
            for i, row in enumerate(reader):
                if self.content_columns:
                    text = " | ".join(str(row.get(c, "")) for c in self.content_columns)
                else:
                    text = " | ".join(str(v) for v in row.values())
                meta: Dict[str, str] = {"source": str(path), "row": str(i)}
                docs.append(Document(content=text, metadata=meta))
        return docs


class WebPageLoader:
    """Load a web page as a Document (requires requests + beautifulsoup4)."""

    def __init__(self, url: str) -> None:
        self.url = url

    def load(self) -> List[Document]:
        import requests  # already in dependencies
        resp = requests.get(self.url, timeout=15)
        resp.raise_for_status()
        try:
            from bs4 import BeautifulSoup  # type: ignore
            soup = BeautifulSoup(resp.text, "html.parser")
            # Remove script/style
            for tag in soup(["script", "style"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
        except ImportError:
            text = resp.text
        return [Document(content=text, metadata={"source": self.url})]
