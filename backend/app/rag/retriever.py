"""Document retrieval module connecting ChromaDB to the LangGraph agent for ledger and financial docs."""

import logging
from typing import Any
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_core.tools import tool

from app.config import settings
from app.rag.ingest import COLLECTION_NAME, get_embedding_function

logger = logging.getLogger(__name__)


def get_vectorstore() -> Chroma:
    """Instantiate and return the Chroma vector store instance."""
    embeddings = get_embedding_function()
    return Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=settings.CHROMA_PATH,
        embedding_function=embeddings,
    )


def retrieve(query: str, k: int = 4) -> list[Document]:
    """Retrieve top-k relevant document chunks for a given query.

    Args:
        query: Natural language search string.
        k: Maximum number of relevant chunks to retrieve.

    Returns:
        list[Document]: Retrieved LangChain Document objects.
    """
    try:
        store = get_vectorstore()
        docs = store.similarity_search(query, k=k)
        return docs
    except Exception as e:
        logger.error("Error during similarity search: %s", str(e))
        return []


@tool
def search_ledger_docs(query: str) -> dict[str, Any]:
    """Search indexed personal financial ledger records, transaction batches, trip expenses, category profiles, and monthly summaries.

    Use this tool when users ask questions such as:
    - What did I spend on the Manang trip or vacation?
    - When did I pay for bike servicing or vehicle maintenance?
    - What transactions did I have with Dad, Roslina, or other contacts?
    - How much salary came from Fonepay or Side Hustles in specific months?
    - What does my spending profile look like for specific categories or lifestyle expenses?

    Args:
        query: Search question or keywords related to ledger transactions, trips, or spending notes.

    Returns:
        dict: Retrieved ledger text excerpts, sources, and plain-English summary.
    """
    logger.info("Executing search_ledger_docs with query: %s", query)
    try:
        docs = retrieve(query, k=4)
        if not docs:
            return {
                "value": [],
                "unit": "documents",
                "method": "chroma_similarity_search",
                "inputs": {"query": query},
                "interpretation": f"No relevant ledger documentation found for query '{query}'.",
            }

        extracted = [
            {
                "source": d.metadata.get("source", "ledger_docs"),
                "category": d.metadata.get("category", ""),
                "type": d.metadata.get("type", "doc"),
                "content": d.page_content.strip(),
            }
            for d in docs
        ]

        summary_snippets = [f"[{e['source']}]: {e['content'][:150]}..." for e in extracted]
        interpretation = (
            f"Found {len(extracted)} relevant ledger excerpts addressing '{query}': "
            + " | ".join(summary_snippets)
        )

        return {
            "value": extracted,
            "unit": "document_chunks",
            "method": "chroma_similarity_search",
            "inputs": {"query": query},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in search_ledger_docs tool: %s", str(exc), exc_info=True)
        return {
            "value": [],
            "unit": "error",
            "method": "chroma_similarity_search",
            "inputs": {"query": query},
            "interpretation": f"Could not retrieve ledger records due to error: {str(exc)}",
        }


@tool
def search_financial_docs(query: str) -> dict[str, Any]:
    """Search authoritative financial documentation, risk glossary definitions, and ledger policy.

    Args:
        query: Search keywords or question relating to financial concepts or guidelines.

    Returns:
        dict: Retrieved text excerpts, source filenames, and summary.
    """
    return search_ledger_docs.invoke({"query": query})
