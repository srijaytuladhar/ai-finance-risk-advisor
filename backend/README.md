# Fintech Portfolio Risk Advisor - Backend Service

FastAPI service powering the hybrid quantitative AI risk advisor, combining LangGraph agent orchestration, deterministic quantitative financial tools (numpy, pandas, yfinance), and local ChromaDB RAG.

## Architecture Overview
1. **Deterministic Core**: All quantitative risk models (VaR, Sharpe ratio, Max Drawdown, Beta, Volatility, Weights) execute exclusively through deterministic Python functions.
2. **LangGraph Agent**: Deconstructs user intent, selects appropriate mathematical tools, and synthesizes tool outputs.
3. **RAG Knowledge Base**: Indexes risk glossaries and investment policy statements into local persistent ChromaDB.

## Quickstart

### 1. Environment Setup
```bash
cd backend
python -m venv .venv

# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
# .venv\Scripts\Activate.ps1

pip install -r requirements.txt
cp .env.example .env
```
Edit `.env` and set your `OPENAI_API_KEY`.

### 2. Run Ingestion (Optional)
On startup, the FastAPI server will automatically verify and ingest markdown documents in `data/docs/` if ChromaDB is empty. You can also run it explicitly:
```bash
python -m app.rag.ingest
```

### 3. Start Development Server
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive Swagger API docs available at: `http://localhost:8000/docs`.

### 4. Run Golden Benchmark Evaluations
```bash
python -m app.evals.run_evals
```
Runs 10 benchmark queries through an LLM-as-a-judge scoring harness evaluating tool execution, numerical fidelity, and synthesis clarity.
