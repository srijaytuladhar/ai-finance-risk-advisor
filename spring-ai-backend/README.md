# Fintech Financial & Ledger Risk Advisor - Spring AI Backend

A high-performance Spring Boot & Spring AI service providing deterministic personal finance arithmetic, authentic Nepalese ledger analytics, and multi-turn conversational AI with automatic tool execution.

This backend serves the exact API endpoints and JSON contracts expected by the React frontend, allowing it to seamlessly replace the Python backend on port `8000`.

---

## Key Features

1. **Deterministic Financial Calculation Engine (`LedgerService`)**:
   - Parses the complete `ledger.json` dataset (5 accounts across Citizen Bank, eSewa, Cash, Prabhu Bank, Laxmi Bank, and 1,430+ authentic transactions).
   - Real-time arithmetic on account balances, weights, income vs. expense, net savings, monthly cashflow, and emergency runway diagnostics.
   - Zero hallucination in numbers: calculations are strictly performed deterministically by Java methods before returning to the LLM or frontend.

2. **Spring AI Agent with Function / Tool Calling (`AdvisorAgentService` & `LedgerTools`)**:
   - Integrated with Spring AI 2.x and OpenAI-compatible API providers (OpenRouter, OpenAI, Ollama).
   - Binds deterministic tools:
     - `get_account_balances`
     - `get_spending_summary`
     - `get_category_breakdown`
     - `query_ledger_transactions`
     - `get_monthly_cashflow`
     - `calculate_financial_health_metrics`
     - `search_ledger_docs`
     - `search_financial_docs`
   - Captures all tool invocations and citations per conversational turn, returning structured `tool_calls` and `sources` to the frontend UI.

3. **Full Compatibility with Frontend**:
   - Runs on `http://localhost:8000` by default.
   - CORS enabled for frontend dev servers (`http://localhost:5173`, `http://127.0.0.1:5173`, `*`).
   - Jackson configured for `snake_case` JSON serialization matching the frontend TypeScript interfaces in `frontend/src/types.ts`.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status and active AI model name |
| `GET` | `/api/portfolio` | Real-time aggregate liquid funds, account distributions, spending categories, monthly cashflow, and transactions |
| `GET` | `/api/ledger` | Alias for `/api/portfolio` |
| `POST` | `/api/chat` | Conversational query execution with Spring AI agent and deterministic tool calling |

---

## Prerequisites & Setup

- **Java**: Java 21 LTS (or Java 17+)
- **Build Tool**: Apache Maven 3.9+ or the included Maven Wrapper (`mvnw.cmd` / `./mvnw`)

### Configuration

Configuration parameters are located in `src/main/resources/application.properties` and can be overridden via environment variables:

| Property / Env Var | Default | Description |
|---|---|---|
| `server.port` | `8000` | HTTP listening port |
| `OPENROUTER_API_KEY` | *(Configured)* | OpenRouter API Key for OpenAI-compatible LLM inference |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Base URL for LLM provider |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | LLM model identifier |

---

## Running the Application

### 1. Start the Spring AI Backend
Using the local Maven installation or Maven Wrapper:

```powershell
cd spring-ai-backend
$env:JAVA_HOME = "C:\Users\LOQ\.jdks\temurin-21.0.11"
& "C:\Users\LOQ\maven\apache-maven-3.9.16\bin\mvn.cmd" spring-boot:run
```

Or using Maven Wrapper:
```powershell
.\mvnw.cmd spring-boot:run
```

### 2. Connect the React Frontend
Since the Spring AI backend runs on port `8000`, start the frontend as normal:
```powershell
cd frontend
npm run dev
```
The frontend at `http://localhost:5173` will immediately communicate with the Spring AI backend without modifying any frontend code.
