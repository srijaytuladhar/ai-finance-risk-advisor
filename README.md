# Fintech Portfolio Risk Advisor

A production-grade conversational AI application where investors and wealth advisors can ask natural-language questions about their investment portfolio and receive quantitatively verified risk analytics and portfolio guidance.

---

## 1. Architecture Flow Diagram

```
+-----------------------------------------------------------------------------------------+
|                                    USER / CLIENT                                        |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                    FRONTEND (React + Vite + TypeScript + Tailwind CSS)                  |
|  - Real-time chat terminal with inline deterministic tool execution badges              |
|  - Live portfolio snapshot table (shares, prices, weights)                              |
|  - Interactive Recharts Donut Chart for sector exposure breakdown                       |
+-----------------------------------------------------------------------------------------+
                                             |  HTTP REST (JSON)
                                             v
+-----------------------------------------------------------------------------------------+
|                             BACKEND (FastAPI + Uvicorn)                                 |
|  - POST /api/chat      (conversational agent invocation)                                |
|  - GET  /api/portfolio (live holdings, weights, & sector exposures)                     |
|  - GET  /api/health    (readiness probe & model status)                                 |
+-----------------------------------------------------------------------------------------+
                                             |
                                             v
+-----------------------------------------------------------------------------------------+
|                              LANGGRAPH ORCHESTRATION                                    |
|                                                                                         |
|        +-------------------+                 +---------------------+                    |
|        |   'agent' Node    | <--- Route ---> |    'tools' Node     |                    |
|        | (Intent & ReAct)  |                 | (Tool Execution)    |                    |
|        +-------------------+                 +---------------------+                    |
|                  |                                      |                               |
+------------------|--------------------------------------|-------------------------------+
                   |                                      |
         +---------+---------+                  +---------+---------+
         |                   |                  |                   |
         v                   v                  v                   v
+----------------+  +-----------------+  +--------------+  +------------------+
|     OPENAI     |  |    CHROMADB     |  | DETERMINISTIC|  |     YFINANCE     |
|  (gpt-4o-mini) |  |   VECTORSTORE   |  | PYTHON TOOLS |  |   MARKET DATA    |
| - Intent       |  | - Risk Glossary |  | - VaR (1y)   |  | - Live quotes    |
| - Synthesis    |  | - Investment    |  | - Sharpe     |  | - Historical 1y  |
|   (NO MATH!)   |  |   Policy (IPS)  |  | - Drawdown   |  |   daily close    |
|                |  |                 |  | - Volatility |  |                  |
|                |  |                 |  | - Beta (SPY) |  |                  |
|                |  |                 |  | - Rebalancing|  |                  |
+----------------+  +-----------------+  +--------------+  +------------------+
```

---

## 2. Why the Hybrid Architecture Matters

Large Language Models (LLMs) are probabilistic pattern matchers. In general NLP tasks, minor statistical variance is acceptable; **in fintech and quantitative wealth management, hallucinated numbers are fatal.**

### The Flaws of Pure LLM Calculations:
- **Calculation Errors**: LLMs struggle with compounding, covariance matrices, quantile percentiles, and square root scaling.
- **Silent Hallucinations**: An LLM might state that a portfolio's 95% 1-day VaR is "0.85%" when the real historical simulation calculates it at "2.45%".
- **Non-reproducible Outputs**: Identical prompts produce divergent numbers across consecutive queries.

### The Hybrid Solution:
This project enforces strict separation of concerns:
1. **The LLM NEVER calculates numbers**: All arithmetic, matrix algebra, statistical percentiles, and market data queries are routed to dedicated, deterministic Python functions using `numpy`, `pandas`, and `yfinance`.
2. **The LLM is restricted to**:
   - Discerning user intent from natural language.
   - Determining which deterministic tool(s) to invoke with what parameters.
   - Synthesizing tool outputs into actionable, plain-English explanations.

---

## 3. Setup & Running Locally

The application requires **no Docker** and runs with two simple terminal commands.

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- OpenAI API Key

---

### Terminal 1: Backend Setup
```bash
# 1. Navigate to backend
cd fintech-risk-advisor/backend

# 2. Create and activate virtual environment
# Linux/macOS:
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell:
# python -m venv .venv
# .venv\Scripts\Activate.ps1

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Open .env and insert your valid OpenAI API key:
# OPENAI_API_KEY=sk-proj-...

# 5. Start the backend server (FastAPI + Uvicorn)
uvicorn app.main:app --reload --port 8000
```
*Note: On first startup, the backend automatically ingests `data/docs/*.md` into local ChromaDB.*

---

### Terminal 2: Frontend Setup
```bash
# 1. Navigate to frontend
cd fintech-risk-advisor/frontend

# 2. Install dependencies
npm install

# 3. Start development server (Vite)
npm run dev
```
Open your browser at **`http://localhost:5173`**.

---

## 4. Running Evaluations

The repository includes a comprehensive 10-question evaluation benchmark testing risk metrics, rebalancing logic, and RAG retrieval using an LLM-as-a-judge scoring methodology:

```bash
cd fintech-risk-advisor/backend
python -m app.evals.run_evals
```

The benchmark evaluates:
1. **Tool Execution Accuracy (0.0 - 1.0)**: Did the agent call the expected deterministic tools without attempting mental arithmetic?
2. **Numerical & Logical Grounding (0.0 - 1.0)**: Are reported values strictly derived from the tool result?
3. **Clarity of Explanation (0.0 - 1.0)**: Is the financial synthesis clear, accurate, and professional?

Detailed results and timestamps are automatically saved to `backend/app/evals/results.json`.

---

## 5. Example Questions to Try

- **Value at Risk**: *"What is my portfolio's VaR at 95% confidence over a 1-day horizon?"*
- **Risk-Adjusted Return**: *"What is my Sharpe ratio and how does it compare to standard benchmarks?"*
- **Downside Risk**: *"What was the maximum drawdown of my portfolio over the last year?"*
- **Systematic Risk**: *"What is my portfolio beta relative to SPY?"*
- **Asset Allocation & Drift**: *"Should I rebalance my portfolio right now?"*
- **Sector Concentration**: *"What is my largest sector exposure and what percentage does it represent?"*
- **RAG Policy Guidance**: *"What does our investment policy statement say about target asset allocation and rebalancing bands?"*
- **RAG Glossary**: *"What does Value at Risk actually mean in plain English?"*

---

## 6. Cost & Latency Notes

- **Model Used**: `gpt-4o-mini` (OpenAI)
  - Input Tokens: ~$0.15 per 1M tokens
  - Output Tokens: ~$0.60 per 1M tokens
- **Embeddings**: `text-embedding-3-small`
  - Input Tokens: ~$0.02 per 1M tokens
- **Tokens per Standard Query**:
  - System prompt + tools schema: ~850 tokens
  - Tool output payload: ~250 - 600 tokens
  - Synthesized response: ~200 - 350 tokens
  - **Estimated Cost per Turn**: `< $0.0008` (less than 1/10th of a cent)
- **Turn Latency**:
  - Pure calculation tools: ~0.8s - 2.5s (includes yfinance download caching)
  - Total end-to-end response: ~1.8s - 3.5s
