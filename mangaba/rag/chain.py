"""
RAGChain: end-to-end retrieval-augmented generation.
"""

from __future__ import annotations

from typing import Any, List, Optional

from mangaba.rag.document import Document
from mangaba.rag.retriever import Retriever


class RAGChain:
    """Combines a Retriever with an LLM to answer questions using retrieved context.

    This class implements retrieval-augmented generation (RAG), which retrieves
    relevant documents from a knowledge base and uses them as context for an LLM
    to generate answers to questions.

    Example::

        chain = RAGChain(retriever=retriever, llm=llm_client)
        answer = chain.query("What is the capital of France?")

    Attributes:
        retriever: The retriever to use for document search.
        llm: The LLM client to use for answer generation.
        template: The prompt template to use for answer generation.
        top_k: The number of documents to retrieve for each query.
    """

    DEFAULT_TEMPLATE = (
        "Answer the question based on the context below.\n\n"
        "Context:\n{context}\n\n"
        "Question: {question}\n\n"
        "Answer:"
    )

    def __init__(
        self,
        retriever: Retriever,
        llm: Any,  # LLMClient
        prompt_template: Optional[str] = None,
        top_k: int = 5,
    ) -> None:
        """Initialize the RAGChain.

        Args:
            retriever: The retriever to use for document search.
            llm: The LLM client to use for answer generation.
            prompt_template: Optional custom prompt template. If not provided,
                uses the default template.
            top_k: The number of documents to retrieve for each query (default: 5).
        """
        self.retriever = retriever
        self.llm = llm
        self.template = prompt_template or self.DEFAULT_TEMPLATE
        self.top_k = top_k

    def query(self, question: str) -> str:
        """Retrieve relevant documents and generate an answer.

        Args:
            question: The question to answer.

        Returns:
            The generated answer as a string.
        """
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        return self.llm.generate_text(prompt)

    def query_with_sources(self, question: str) -> dict:
        """Return answer plus the source documents.

        Args:
            question: The question to answer.

        Returns:
            A dictionary with keys "answer" (the generated answer) and "sources"
            (the list of retrieved documents).
        """
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        answer = self.llm.generate_text(prompt)
        return {"answer": answer, "sources": docs}

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        """Format a list of documents into a context string.

        Args:
            docs: The documents to format.

        Returns:
            A string with document contents separated by "---".
        """
        return "\n---\n".join(d.content for d in docs)
