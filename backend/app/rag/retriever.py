"""Document retrieval module connecting ChromaDB to the LangGraph agent."""

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


def retrieve(query: str, k: int = 3) -> list[Document]:
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
def search_financial_docs(query: str) -> dict[str, Any]:
    """Search authoritative financial documentation, risk glossary definitions, and the investment policy statement.

    Use this tool when users ask conceptual questions such as:
    - What is Value at Risk (VaR), Sharpe Ratio, Maximum Drawdown, Volatility, or Beta?
    - What are the portfolio investment policy rules, target allocations, risk tolerance, or rebalancing trigger bands?

    Args:
        query: Search keywords or question relating to risk concepts or investment policies.

    Returns:
        dict: Retrieved text excerpts, source filenames, and plain-English summary.
    """
    logger.info("Executing search_financial_docs with query: %s", query)
    try:
        docs = retrieve(query, k=3)
        if not docs:
            return {
                "value": [],
                "unit": "documents",
                "method": "chroma_similarity_search",
                "inputs": {"query": query},
                "interpretation": f"No relevant financial documentation found for query '{query}'.",
            }

        extracted = [
            {
                "source": d.metadata.get("source", "knowledge_base"),
                "content": d.page_content.strip(),
            }
            for d in docs
        ]

        summary_snippets = [f"[{e['source']}]: {e['content'][:150]}..." for e in extracted]
        interpretation = (
            f"Found {len(extracted)} relevant documentation excerpts addressing '{query}': "
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
        logger.error("Error in search_financial_docs tool: %s", str(exc), exc_info=True)
        return {
            "value": [],
            "unit": "error",
            "method": "chroma_similarity_search",
            "inputs": {"query": query},
            "interpretation": f"Could not retrieve documents due to error: {str(exc)}",
        }
