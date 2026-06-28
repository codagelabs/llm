"""
RAG core: embedding retrieval + LLM answer generation.
"""

import os
from dataclasses import dataclass, field

import chromadb
from chromadb.utils import embedding_functions
from litellm import completion
from openai import OpenAI

from src.config import (
    CHROMA_DB_PATH,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    LLM_MODEL,
    RAG_N_RESULTS,
    SYSTEM_PROMPT,
    QUERY_REWRITE_PROMPT,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Result:
    """A retrieved chunk with its content and metadata."""

    page_content: str
    metadata: dict = field(default_factory=dict)

    def __repr__(self) -> str:
        preview = self.page_content[:120].replace("\n", " ")
        return f"Result(match={self.metadata.get('match_id')}, type={self.metadata.get('chunk_type')}, preview='{preview}…')"


# ---------------------------------------------------------------------------
# RAG engine
# ---------------------------------------------------------------------------

class IPLRagEngine:
    """
    Retrieval-Augmented Generation engine for IPL cricket data.

    Parameters
    ----------
    chroma_path : str
        Path to the ChromaDB persistent store.
    collection_name : str
        Name of the ChromaDB collection.
    """

    def __init__(
        self,
        chroma_path: str = CHROMA_DB_PATH,
        collection_name: str = COLLECTION_NAME,
    ) -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise EnvironmentError("OPENAI_API_KEY is not set.")

        # OpenAI client (for embeddings)
        self._openai = OpenAI(api_key=api_key)

        # ChromaDB
        self._openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=api_key,
            model_name=EMBEDDING_MODEL,
        )
        client = chromadb.PersistentClient(path=chroma_path)
        self._collection = client.get_collection(
            name=collection_name,
            embedding_function=self._openai_ef,
        )
        print(f"Connected to ChromaDB collection '{collection_name}' "
              f"({self._collection.count()} documents).")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_context(self, question: str, n_results: int = RAG_N_RESULTS) -> list[Result]:
        """Embed *question* and retrieve the top-k matching chunks."""
        embedding = (
            self._openai.embeddings.create(model=EMBEDDING_MODEL, input=[question])
            .data[0]
            .embedding
        )
        results = self._collection.query(
            query_embeddings=[embedding], n_results=n_results
        )
        chunks: list[Result] = []
        for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
            chunks.append(Result(page_content=doc, metadata=meta))
        return chunks

    def rewrite_query(self, question: str, history: list[dict] | None = None) -> str:
        """
        Use the LLM to rewrite the user question into a focused KB query.
        """
        history_str = "\n".join(
            f"{msg['role'].upper()}: {msg['content']}" for msg in (history or [])
        )
        prompt = QUERY_REWRITE_PROMPT.format(history=history_str, question=question)
        response = completion(
            model=LLM_MODEL,
            messages=[{"role": "system", "content": prompt}],
        )
        return response.choices[0].message.content.strip()

    def answer_question(
        self,
        question: str,
        history: list[dict] | None = None,
        verbose: bool = False,
    ) -> str:
        """
        Full RAG pipeline:
        1. Rewrite question → focused KB query
        2. Retrieve context chunks
        3. Build prompt with context + conversation history
        4. Generate answer via LLM

        Returns the LLM answer string.
        """
        history = history or []

        # 1. Query rewriting
        kb_query = self.rewrite_query(question, history)
        if verbose:
            print(f"[KB query] {kb_query}")

        # 2. Retrieval
        chunks = self.fetch_context(kb_query)
        if verbose:
            print(f"[Retrieved {len(chunks)} chunks]")

        # 3. Build messages
        context = "\n\n".join(
            f"Extract from {c.metadata.get('match_id', 'unknown')}:\n{c.page_content}"
            for c in chunks
        )
        system_prompt = SYSTEM_PROMPT.format(context=context)
        messages = (
            [{"role": "system", "content": system_prompt}]
            + history
            + [{"role": "user", "content": question}]
        )

        # 4. Generate answer
        response = completion(model=LLM_MODEL, messages=messages)
        return response.choices[0].message.content
