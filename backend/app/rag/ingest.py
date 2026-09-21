"""Document ingestion pipeline for indexing personal ledger data and financial docs into ChromaDB."""

import hashlib
import json
import logging
from pathlib import Path
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import settings

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
DOCS_DIR = DATA_DIR / "docs"
LEDGER_PATH = DATA_DIR / "ledger.json"
COLLECTION_NAME = "fintech_risk_docs"


def get_embedding_function():
    """Return embedding function instance using Google Gemini or OpenAI."""
    if settings.GEMINI_API_KEY or "gemini" in settings.MODEL_NAME.lower():
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        return GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            google_api_key=settings.GEMINI_API_KEY,
        )
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=settings.OPENAI_API_KEY,
    )


def build_ledger_documents() -> list[Document]:
    """Parse ledger.json into semantic Document chunks for vector indexing."""
    if not LEDGER_PATH.exists():
        logger.warning("ledger.json not found at %s", LEDGER_PATH)
        return []

    try:
        with open(LEDGER_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        logger.error("Failed to read ledger.json for RAG: %s", str(exc))
        return []

    accounts = data.get("accounts", [])
    transactions = data.get("transactions", [])
    categories = data.get("categories", [])
    account_map = {acc["id"]: acc.get("name", "Unknown") for acc in accounts if "id" in acc}

    docs: list[Document] = []

    # 1. Accounts & Net Worth Overview Document
    total_balance = sum(float(a.get("balance", 0.0)) for a in accounts)
    acc_lines = []
    for a in accounts:
        acc_lines.append(
            f"- {a.get('name')} ({a.get('type')}): Balance Rs. {float(a.get('balance', 0.0)):,.2f} "
            f"(Initial: Rs. {float(a.get('initialBalance', 0.0)):,.2f}, Color: {a.get('color')})"
        )
    accounts_content = (
        "# User Financial Accounts and Net Worth Profile\n"
        f"Total Liquid Net Worth: Rs. {total_balance:,.2f} across {len(accounts)} accounts.\n"
        "Account Details:\n" + "\n".join(acc_lines) + "\n\n"
        "Primary account is Citizen Bank, holding the vast majority of liquid funds. "
        "eSewa is the default digital payment wallet. Cash is held for physical transactions."
    )
    docs.append(Document(page_content=accounts_content, metadata={"source": "ledger_accounts", "type": "accounts_summary"}))

    # 2. Income and Earnings Profile Document
    incomes_by_cat: dict[str, float] = {}
    total_income = 0.0
    for t in transactions:
        if t.get("type") == "Income":
            amt = float(t.get("amount", 0.0))
            c = t.get("category") or t.get("description") or "Other Income"
            incomes_by_cat[c] = incomes_by_cat.get(c, 0.0) + amt
            total_income += amt

    sorted_incomes = sorted(incomes_by_cat.items(), key=lambda x: x[1], reverse=True)
    inc_lines = [f"- {c}: Rs. {amt:,.2f} ({(amt/total_income*100) if total_income > 0 else 0:.1f}%)" for c, amt in sorted_incomes]
    income_content = (
        "# User Income Sources and Earnings Overview\n"
        f"Total Lifetime Income: Rs. {total_income:,.2f} from Jan 2026 to Sep 2026.\n"
        "Income Streams Breakdown:\n" + "\n".join(inc_lines) + "\n\n"
        "Primary salary is received from Fonepay into Citizen Bank. Secondary income comes from Side Hustle and regular deposits."
    )
    docs.append(Document(page_content=income_content, metadata={"source": "ledger_income", "type": "income_summary"}))

    # 3. Monthly Financial Snapshots
    monthly_data: dict[str, dict[str, Any]] = {}
    for t in transactions:
        d_str = t.get("date", "")
        if not d_str or len(d_str) < 7:
            continue
        m = d_str[:7]
        if m not in monthly_data:
            monthly_data[m] = {"income": 0.0, "expense": 0.0, "categories": {}, "tx_count": 0}
        amt = float(t.get("amount", 0.0))
        ttype = t.get("type")
        monthly_data[m]["tx_count"] += 1
        if ttype == "Income":
            monthly_data[m]["income"] += amt
        elif ttype == "Expense":
            monthly_data[m]["expense"] += amt
            cat = t.get("category") or "Other"
            monthly_data[m]["categories"][cat] = monthly_data[m]["categories"].get(cat, 0.0) + amt

    for m, mdata in sorted(monthly_data.items()):
        inc = mdata["income"]
        exp = mdata["expense"]
        net = inc - exp
        top_cats = sorted(mdata["categories"].items(), key=lambda x: x[1], reverse=True)[:5]
        top_cats_str = ", ".join([f"{c} (Rs. {a:,.0f})" for c, a in top_cats])
        m_content = (
            f"# Monthly Financial Snapshot: {m}\n"
            f"- Total Income: Rs. {inc:,.2f}\n"
            f"- Total Expenses: Rs. {exp:,.2f}\n"
            f"- Net Cash Flow: Rs. {net:,.2f} ({'Surplus' if net >= 0 else 'Deficit'})\n"
            f"- Transaction Count: {mdata['tx_count']}\n"
            f"- Top Expense Drivers: {top_cats_str if top_cats_str else 'None'}\n"
        )
        docs.append(Document(page_content=m_content, metadata={"source": f"monthly_{m}", "month": m, "type": "monthly_snapshot"}))

    # 4. Deep-dive on Key Categories (Renovation, Technology, Eating Out, Gift, ACS, Manang, Bike, Chiya, Love)
    cat_txs: dict[str, list[dict[str, Any]]] = {}
    for t in transactions:
        c = t.get("category") or "Uncategorized"
        cat_txs.setdefault(c, []).append(t)

    for cat_name, tx_list in cat_txs.items():
        total_cat_amt = sum(float(x.get("amount", 0.0)) for x in tx_list)
        # Only create dedicated category doc if total >= 5000 or significant
        if total_cat_amt >= 5000 or len(tx_list) >= 10:
            sample_txs = tx_list[:15]
            sample_lines = []
            for st in sample_txs:
                st_date = st.get("date", "")[:10]
                st_amt = float(st.get("amount", 0.0))
                st_desc = st.get("description") or "No description"
                st_acc = account_map.get(st.get("accountId", ""), "Account")
                sample_lines.append(f"  - {st_date} | Rs. {st_amt:,.2f} | {st_desc} | Account: {st_acc}")
            cat_doc = (
                f"# Spending Category Profile: {cat_name}\n"
                f"Total Amount: Rs. {total_cat_amt:,.2f} across {len(tx_list)} transactions.\n"
                f"Recent Notable Transactions:\n" + "\n".join(sample_lines) + "\n"
            )
            docs.append(Document(
                page_content=cat_doc,
                metadata={"source": f"category_{cat_name.lower().replace(' ', '_')}", "category": cat_name, "type": "category_profile"}
            ))

    # 5. Batched Recent Transactions for granular search
    batch_size = 15
    for i in range(0, min(len(transactions), 300), batch_size):
        batch = transactions[i:i + batch_size]
        b_lines = []
        for bt in batch:
            b_date = bt.get("date", "")[:10]
            b_type = bt.get("type", "Expense")
            b_amt = float(bt.get("amount", 0.0))
            b_cat = bt.get("category", "General")
            b_desc = bt.get("description", "")
            b_acc = account_map.get(bt.get("accountId", ""), "Account")
            b_lines.append(f"- {b_date} | {b_type} | Rs. {b_amt:,.2f} | {b_cat} | {b_desc} | via {b_acc}")
        batch_content = (
            f"# Ledger Transaction Log (Batch {i // batch_size + 1})\n"
            + "\n".join(b_lines)
        )
        docs.append(Document(
            page_content=batch_content,
            metadata={"source": f"transaction_batch_{i // batch_size + 1}", "type": "transaction_batch"}
        ))

    logger.info("Generated %d semantic documents from ledger.json", len(docs))
    return docs


def ingest_documents(force: bool = False) -> int:
    """Ingest both ledger.json and reference markdown documents into ChromaDB."""
    logger.info("Starting document ingestion...")

    embeddings = get_embedding_function()
    vectorstore = Chroma(
        collection_name=COLLECTION_NAME,
        persist_directory=settings.CHROMA_PATH,
        embedding_function=embeddings,
    )

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

    raw_docs: list[Document] = []

    # 1. Build documents from ledger.json
    ledger_docs = build_ledger_documents()
    raw_docs.extend(ledger_docs)

    # 2. Build documents from markdown files in data/docs if present
    if DOCS_DIR.exists():
        md_files = list(DOCS_DIR.glob("*.md"))
        for file_path in md_files:
            try:
                loader = TextLoader(str(file_path), encoding="utf-8")
                loaded = loader.load()
                for doc in loaded:
                    doc.metadata["source"] = file_path.name
                raw_docs.extend(loaded)
                logger.info("Loaded document: %s", file_path.name)
            except Exception as e:
                logger.error("Failed to load document %s: %s", file_path, str(e))

    if not raw_docs:
        logger.warning("No documents available to ingest.")
        return 0

    # Chunk any long documents
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=60,
        separators=["\n# ", "\n## ", "\n### ", "\n\n", "\n", " ", ""],
    )
    chunks = text_splitter.split_documents(raw_docs)
    logger.info("Generated %d chunks from %d raw documents", len(chunks), len(raw_docs))

    # Generate deterministic IDs for idempotency
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
