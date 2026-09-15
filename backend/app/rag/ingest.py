"""Document ingestion pipeline for indexing risk glossaries and policy docs into ChromaDB."""

import hashlib
import logging
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "docs"
COLLECTION_NAME = "fintech_risk_docs"


def get_embedding_function() -> OpenAIEmbeddings:
    """Return OpenAI embeddings instance using text-embedding-3-small."""
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.OPENAI_API_KEY,
    )


def ingest_documents(force: bool = False) -> int:
    """Read markdown documents from data/docs, chunk, embed, and store in ChromaDB.

    This function is idempotent. If the collection already contains chunks and force=False,
    it skips re-embedding to save API credits and time.

    Args:
        force: If True, clears existing vectorstore collection and re-indexes all files.

    Returns:
        int: Number of document chunks indexed or existing in the vector store.
    """
    logger.info("Starting document ingestion from %s", DOCS_DIR)

    if not DOCS_DIR.exists():
        logger.warning("Docs directory %s does not exist. Creating it.", DOCS_DIR)
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        return 0

    embeddings = get_embedding_function()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=settings.CHROMA_PATH,
        embedding_function=embeddings,
    )

    # Check existing collection count
    try:
        existing_count = vectorstore._collection.count()
        if existing_count > 0 and not force:
            logger.info("ChromaDB collection already contains %d documents. Skipping re-ingestion.", existing_count)
            return existing_count
        elif force and existing_count > 0:
            logger.info("Force flag set. Resetting ChromaDB collection %s.", COLLECTION_NAME)
            vectorstore.delete_collection()
            vectorstore = Chroma(
                collection_name=COLLECTION_NAME,
                persist_directory=settings.CHROMA_PATH,
                embedding_function=embeddings,
            )
    except Exception as e:
        logger.warning("Error checking collection status: %s", str(e))

    # Read all markdown files
    md_files = list(DOCS_DIR.glob("*.md"))
    if not md_files:
        logger.warning("No markdown files found in %s", DOCS_DIR)
        return 0

    raw_docs = []
    for file_path in md_files:
        try:
            loader = TextLoader(str(file_path), encoding="utf-8")
            loaded = loader.load()
            for doc in loaded:
                doc.metadata["source"] = file_path.name
            raw_docs.extend(loaded)
            logger.info("Loaded document: %s (%d chars)", file_path.name, sum(len(d.page_content) for d in loaded))
        except Exception as e:
            logger.error("Failed to load document %s: %s", file_path, str(e))

    # Chunk with RecursiveCharacterTextSplitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(raw_docs)
    logger.info("Generated %d chunks from %d raw documents", len(chunks), len(raw_docs))

    # Deterministic IDs for idempotency
    ids = []
    for chunk in chunks:
        source = chunk.metadata.get("source", "doc")
        content_hash = hashlib.md5(chunk.page_content.encode("utf-8")).hexdigest()[:12]
        chunk_id = f"{source}_{content_hash}"
        ids.append(chunk_id)

    vectorstore.add_documents(documents=chunks, ids=ids)
    vectorstore.persist()
    total_count = vectorstore._collection.count()
    logger.info("Ingestion completed successfully. Total indexed chunks: %d", total_count)
    return total_count


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    count = ingest_documents(force=True)
    print(f"Successfully ingested {count} chunks into ChromaDB at {settings.CHROMA_PATH}")
