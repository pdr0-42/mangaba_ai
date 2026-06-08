"""
Document loaders for Mangaba AI RAG pipeline.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Optional

from mangaba.rag.document import Document


class TextLoader:
    """Load a plain-text file as a single Document.

    Attributes:
        file_path: The path to the text file to load.
        encoding: The file encoding (default: "utf-8").
    """

    def __init__(self, file_path: str, encoding: str = "utf-8") -> None:
        """Initialize the TextLoader.

        Args:
            file_path: The path to the text file to load.
            encoding: The file encoding (default: "utf-8").
        """
        self.file_path = file_path
        self.encoding = encoding

    def load(self) -> List[Document]:
        """Load the text file as a Document.

        Returns:
            A list containing a single Document with the file content.
        """
        path = Path(self.file_path)
        text = path.read_text(encoding=self.encoding)
        return [Document(content=text, metadata={"source": str(path)})]


class CSVLoader:
    """Load a CSV file, creating a Document for each row.

    Attributes:
        file_path: The path to the CSV file to load.
        content_columns: Optional list of column names to use as content.
            If not provided, all columns are joined.
        encoding: The file encoding (default: "utf-8").
    """

    def __init__(
        self,
        file_path: str,
        content_columns: Optional[List[str]] = None,
        encoding: str = "utf-8",
    ) -> None:
        """Initialize the CSVLoader.

        Args:
            file_path: The path to the CSV file to load.
            content_columns: Optional list of column names to use as content.
                If not provided, all columns are joined.
            encoding: The file encoding (default: "utf-8").
        """
        self.file_path = file_path
        self.content_columns = content_columns
        self.encoding = encoding

    def load(self) -> List[Document]:
        """Load the CSV file as Documents.

        Returns:
            A list of Documents, one for each row in the CSV file.
        """
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
    """Load a web page as a Document.

    This loader requires the requests and beautifulsoup4 packages.

    Attributes:
        url: The URL of the web page to load.
    """

    def __init__(self, url: str) -> None:
        """Initialize the WebPageLoader.

        Args:
            url: The URL of the web page to load.
        """
        self.url = url

    def load(self) -> List[Document]:
        """Load the web page as a Document.

        Returns:
            A list containing a single Document with the web page content.

        Raises:
            requests.HTTPError: If the HTTP request fails.
        """
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
