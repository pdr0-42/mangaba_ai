"""
RAGChain: end-to-end retrieval-augmented generation.
"""

from __future__ import annotations

from typing import Any, List, Optional

from mangaba.rag.document import Document
from mangaba.rag.retriever import Retriever


class RAGChain:
    """Combines a Retriever with an LLM to answer questions using retrieved context.

    Example::

        chain = RAGChain(retriever=retriever, llm=llm_client)
        answer = chain.query("What is the capital of France?")
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
        self.retriever = retriever
        self.llm = llm
        self.template = prompt_template or self.DEFAULT_TEMPLATE
        self.top_k = top_k

    def query(self, question: str) -> str:
        """Retrieve relevant documents and generate an answer."""
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        return self.llm.generate_text(prompt)

    def query_with_sources(self, question: str) -> dict:
        """Return answer plus the source documents."""
        docs = self.retriever.search(question, top_k=self.top_k)
        context = self._format_context(docs)
        prompt = self.template.format(context=context, question=question)
        answer = self.llm.generate_text(prompt)
        return {"answer": answer, "sources": docs}

    @staticmethod
    def _format_context(docs: List[Document]) -> str:
        return "\n---\n".join(d.content for d in docs)
