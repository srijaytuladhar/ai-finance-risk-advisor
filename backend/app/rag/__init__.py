"""Retrieval-Augmented Generation (RAG) module for financial documentation."""

from app.rag.ingest import ingest_documents
from app.rag.retriever import retrieve, search_financial_docs

__all__ = ["ingest_documents", "retrieve", "search_financial_docs"]
