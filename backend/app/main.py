"""FastAPI backend server for Fintech Financial & Ledger Risk Advisor."""

import logging
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import run_agent
from app.config import settings
from app.models.schemas import (
    AccountItem,
    CategorySummary,
    ChatRequest,
    ChatResponse,
    Holding,
    MonthlyCashflow,
    PortfolioResponse,
    TransactionRecord,
)
from app.rag.ingest import ingest_documents
from app.rag.retriever import get_vectorstore
from app.tools.ledger_tools import (
    get_account_balances,
    get_category_breakdown,
    get_monthly_cashflow,
    get_spending_summary,
    query_ledger_transactions,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to verify and initialize ChromaDB on startup."""
    logger.info("Initializing Fintech Financial & Ledger Risk Advisor backend...")
    try:
        store = get_vectorstore()
        count = store._collection.count()
        logger.info("ChromaDB vector collection exists with %d indexed chunks.", count)
        if count == 0:
            logger.info("Vector collection is empty. Triggering automated ingestion of ledger.json and docs...")
            ingested_count = ingest_documents(force=False)
            logger.info("Automated ingestion complete. Indexed %d chunks.", ingested_count)
    except Exception as exc:
        logger.warning(
            "Could not verify or auto-ingest into ChromaDB on startup (%s). "
            "Please ensure GEMINI_API_KEY or OPENAI_API_KEY is configured.",
            str(exc),
        )
    yield
    logger.info("Shutting down Fintech Financial & Ledger Risk Advisor backend...")


app = FastAPI(
    title="Fintech Financial & Ledger Risk Advisor API",
    description="Conversational AI with deterministic personal finance calculations, ledger analytics, and RAG guidance.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Health check endpoint to verify backend operational readiness."""
    return {
        "status": "ok",
        "service": "Fintech Financial & Ledger Risk Advisor",
        "model": settings.MODEL_NAME,
    }


def _build_ledger_portfolio_response() -> PortfolioResponse:
    """Helper to assemble the unified portfolio and ledger analytics response."""
    balances_val = get_account_balances.invoke({}).get("value", {})
    spending_val = get_spending_summary.invoke({}).get("value", {})
    category_val = get_category_breakdown.invoke({"top_n": 10}).get("value", {})
    cashflow_val = get_monthly_cashflow.invoke({}).get("value", {})
    tx_val = query_ledger_transactions.invoke({"limit": 10}).get("value", {})

    raw_accounts = balances_val.get("accounts", [])
    total_balance = float(balances_val.get("total_balance", 0.0))

    accounts_list: list[AccountItem] = [
        AccountItem(
            id=str(a.get("id", "")),
            name=a.get("name", "Account"),
            type=a.get("type", "Bank"),
            balance=float(a.get("balance", 0.0)),
            initial_balance=float(a.get("initial_balance", 0.0)),
            weight=float(a.get("weight", 0.0)),
            color=a.get("color", "#6366f1"),
            is_default=bool(a.get("is_default", False)),
        )
        for a in raw_accounts
    ]

    categories_list: list[CategorySummary] = [
        CategorySummary(
            category=c.get("category", "General"),
            amount=float(c.get("amount", 0.0)),
            percentage=float(c.get("percentage", 0.0)),
            count=int(c.get("count", 0)),
            color=c.get("color"),
            icon=c.get("icon"),
        )
        for c in category_val.get("top_categories", [])
    ]

    monthly_list: list[MonthlyCashflow] = [
        MonthlyCashflow(
            month=m.get("month", ""),
            income=float(m.get("income", 0.0)),
            expense=float(m.get("expense", 0.0)),
            net=float(m.get("net", 0.0)),
        )
        for m in cashflow_val.get("monthly_cashflow", [])
    ]

    recent_txs: list[TransactionRecord] = [
        TransactionRecord(
            id=str(t.get("id", "")),
            date=t.get("date", ""),
            type=t.get("type", "Expense"),
            amount=float(t.get("amount", 0.0)),
            description=t.get("description", ""),
            category=t.get("category", ""),
            account_name=t.get("account", "Account"),
        )
        for t in tx_val.get("transactions", [])
    ]

    # Map accounts to Holdings format for backward compatibility
    holdings: list[Holding] = [
        Holding(
            ticker=a.name,
            shares=1.0,
            price=a.balance,
            value=a.balance,
            weight=a.weight,
            sector=a.type,
        )
        for a in accounts_list
    ]

    weights_dict = {a.name: a.weight for a in accounts_list}
    sectors_dict = {c.category: c.percentage for c in categories_list}

    return PortfolioResponse(
        total_balance=total_balance,
        total_income=float(spending_val.get("total_income", 0.0)),
        total_expense=float(spending_val.get("total_expense", 0.0)),
        net_cashflow=float(spending_val.get("net_savings", 0.0)),
        savings_rate=float(spending_val.get("savings_rate_pct", 0.0)),
        transaction_count=int(spending_val.get("transaction_count", 0)),
        accounts=accounts_list,
        top_categories=categories_list,
        monthly_cashflow=monthly_list,
        recent_transactions=recent_txs,
        holdings=holdings,
        cash=total_balance,
        total_value=total_balance,
        weights=weights_dict,
        sectors=sectors_dict,
    )


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio() -> PortfolioResponse:
    """Retrieve the current ledger snapshot, including account balances, spending, and cash flow analytics."""
    try:
        return _build_ledger_portfolio_response()
    except Exception as exc:
        logger.error("Failed to retrieve portfolio data: %s", str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ledger portfolio: {str(exc)}") from exc


@app.get("/api/ledger", response_model=PortfolioResponse)
def get_ledger() -> PortfolioResponse:
    """Dedicated endpoint to retrieve ledger accounts, category breakdown, and monthly cashflow."""
    return get_portfolio()


@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> ChatResponse:
    """Process natural-language user queries through the LangGraph deterministic risk agent."""
    if not request.message.strip():
        raise HTTPException(status_code=400, detail="User message cannot be empty.")

    try:
        logger.info("Processing user query: '%s'", request.message)
        result = run_agent(message=request.message, history=request.history)
        return ChatResponse(
            response=result["response"],
            tool_calls=result["tool_calls"],
            sources=result["sources"],
        )
    except Exception as exc:
        logger.error("Chat agent execution encountered an error: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Agent reasoning failed: {str(exc)}",
        ) from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
