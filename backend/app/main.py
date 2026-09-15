"""FastAPI backend server for Fintech Portfolio Risk Advisor."""

import logging
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.agent.graph import run_agent
from app.config import settings
from app.models.schemas import ChatRequest, ChatResponse, Holding, PortfolioResponse
from app.rag.ingest import ingest_documents
from app.rag.retriever import get_vectorstore
from app.tools.portfolio_tools import calculate_weights, get_sector_exposure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager to verify and initialize ChromaDB on startup."""
    logger.info("Initializing Fintech Portfolio Risk Advisor backend...")
    try:
        store = get_vectorstore()
        count = store._collection.count()
        logger.info("ChromaDB vector collection exists with %d indexed chunks.", count)
        if count == 0:
            logger.info("Vector collection is empty. Triggering automated ingestion of data/docs...")
            ingested_count = ingest_documents(force=False)
            logger.info("Automated ingestion complete. Indexed %d chunks.", ingested_count)
    except Exception as exc:
        logger.warning(
            "Could not verify or auto-ingest into ChromaDB on startup (%s). "
            "Please ensure GEMINI_API_KEY or OPENAI_API_KEY is configured.",
            str(exc),
        )
    yield
    logger.info("Shutting down Fintech Portfolio Risk Advisor backend...")


app = FastAPI(
    title="Fintech Portfolio Risk Advisor API",
    description="Conversational AI with deterministic quantitative risk calculations and RAG guidance.",
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
        "service": "Fintech Portfolio Risk Advisor",
        "model": settings.MODEL_NAME,
    }


@app.get("/api/portfolio", response_model=PortfolioResponse)
def get_portfolio() -> PortfolioResponse:
    """Retrieve the current portfolio snapshot, including live valuations, weights, and sector distribution."""
    try:
        weights_res = calculate_weights.invoke({})
        val = weights_res.get("value", {})
        holdings_detail = val.get("holdings_detail", [])
        cash = float(val.get("cash", 0.0))
        total_value = float(val.get("total_value", 0.0))
        weights_dict = val.get("weights", {})

        sector_res = get_sector_exposure.invoke({})
        sec_val = sector_res.get("value", {})
        sector_weights = sec_val.get("sector_weights", {})

        holdings: list[Holding] = []
        for hd in holdings_detail:
            holdings.append(
                Holding(
                    ticker=hd["ticker"],
                    shares=hd["shares"],
                    price=hd["price"],
                    value=hd["value"],
                    weight=hd["weight"],
                    sector=hd.get("sector", "Equities"),
                )
            )

        return PortfolioResponse(
            holdings=holdings,
            cash=cash,
            total_value=total_value,
            weights=weights_dict,
            sectors=sector_weights,
        )
    except Exception as exc:
        logger.error("Failed to retrieve portfolio data: %s", str(exc), exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve portfolio: {str(exc)}") from exc


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
