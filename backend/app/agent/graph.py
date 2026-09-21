"""LangGraph ReAct agent orchestration with deterministic tool binding."""

import json
import logging
import time
from typing import Any, Literal
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.config import settings
from app.rag.retriever import search_financial_docs, search_ledger_docs
from app.tools.ledger_tools import (
    calculate_financial_health_metrics,
    get_account_balances,
    get_category_breakdown,
    get_monthly_cashflow,
    get_spending_summary,
    query_ledger_transactions,
)
from app.tools.market_tools import get_current_prices, get_price_history
from app.tools.portfolio_tools import (
    calculate_weights,
    get_portfolio_holdings,
    get_sector_exposure,
    suggest_rebalance,
)
from app.tools.risk_tools import (
    calculate_beta,
    calculate_max_drawdown,
    calculate_sharpe,
    calculate_var,
    calculate_volatility,
)

logger = logging.getLogger(__name__)

# Complete suite of deterministic ledger tools + market tools + RAG retriever tools
AGENT_TOOLS = [
    get_account_balances,
    get_spending_summary,
    get_category_breakdown,
    query_ledger_transactions,
    get_monthly_cashflow,
    calculate_financial_health_metrics,
    search_ledger_docs,
    search_financial_docs,
    calculate_var,
    calculate_sharpe,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_beta,
    get_portfolio_holdings,
    calculate_weights,
    get_sector_exposure,
    suggest_rebalance,
    get_current_prices,
    get_price_history,
]

TOOL_MAP = {t.name: t for t in AGENT_TOOLS}


def build_gemini_model():
    """Build Google Gemini chat model."""
    if not settings.GEMINI_API_KEY:
        return None
    model_name = getattr(settings, "GEMINI_MODEL", "") or (
        settings.MODEL_NAME if "gemini" in settings.MODEL_NAME.lower() else "gemini-3.6-flash"
    )
    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=0.0,
    )


def build_openrouter_model():
    """Build OpenRouter chat model with OpenAI-compatible API."""
    if not settings.OPENROUTER_API_KEY:
        return None
    model_name = getattr(settings, "OPENROUTER_MODEL", "") or "openai/gpt-4o-mini"
    base_url = getattr(settings, "OPENROUTER_BASE_URL", "") or "https://openrouter.ai/api/v1"
    return ChatOpenAI(
        base_url=base_url,
        api_key=settings.OPENROUTER_API_KEY,
        model=model_name,
        temperature=0.0,
    )


def build_openai_model():
    """Build OpenAI chat model."""
    if not settings.OPENAI_API_KEY:
        return None
    model_name = getattr(settings, "OPENAI_MODEL", "") or (
        settings.MODEL_NAME if "gpt" in settings.MODEL_NAME.lower() else "gpt-4o-mini"
    )
    return ChatOpenAI(
        model=model_name,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
        streaming=False,
    )


def build_huggingface_model():
    """Build Hugging Face serverless chat model."""
    if not settings.HUGGINGFACE_API_KEY:
        return None
    model_name = getattr(settings, "HUGGINGFACE_MODEL", "") or (
        settings.MODEL_NAME if "/" in settings.MODEL_NAME else "Qwen/Qwen2.5-72B-Instruct"
    )
    return ChatOpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=settings.HUGGINGFACE_API_KEY,
        model=model_name,
        temperature=0.0,
    )


PROVIDER_COOLDOWNS: dict[str, float] = {}
COOLDOWN_DURATION_SECONDS = 60.0


def get_candidate_models() -> list[tuple[str, Any]]:
    """Return prioritized candidate models bound with deterministic tools.

    Priority order:
    1. Gemini (Default first)
    2. OpenRouter (Secondary fast fallback)
    3. OpenAI (Tertiary fallback)
    4. Hugging Face (Quaternary fallback)
    """
    provider = settings.LLM_PROVIDER.lower().strip()

    builders = {
        "gemini": ("gemini", build_gemini_model),
        "openrouter": ("openrouter", build_openrouter_model),
        "openai": ("openai", build_openai_model),
        "huggingface": ("huggingface", build_huggingface_model),
    }

    all_providers = ["gemini", "openrouter", "openai", "huggingface"]

    # If a specific single provider is explicitly set and not fallback/auto
    if provider in builders:
        order = [provider] + [p for p in all_providers if p != provider]
    else:
        # Default priority: gemini -> openrouter -> openai -> huggingface
        order = all_providers

    candidates: list[tuple[str, Any]] = []
    now = time.time()
    for name in order:
        # Check if provider is currently in cooldown from a recent quota limit
        if name in PROVIDER_COOLDOWNS and PROVIDER_COOLDOWNS[name] > now:
            remaining = int(PROVIDER_COOLDOWNS[name] - now)
            logger.info("Provider '%s' is in temporary cooldown (%ds remaining); skipping to next candidate.", name, remaining)
            continue

        _, builder_fn = builders[name]
        try:
            model = builder_fn()
            if model is not None:
                candidates.append((name, model.bind_tools(AGENT_TOOLS)))
        except Exception as exc:
            logger.warning("Failed to initialize LLM provider '%s': %s", name, str(exc))

    return candidates


def get_llm():
    """Instantiate the primary chat model with LangChain fallbacks configured."""
    candidates = get_candidate_models()
    if not candidates:
        raise RuntimeError("No LLM providers are configured with valid API keys.")

    primary_name, primary_llm = candidates[0]
    fallback_llms = [m for _, m in candidates[1:]]

    if fallback_llms:
        return primary_llm.with_fallbacks(fallback_llms)
    return primary_llm


def agent_node(state: AgentState) -> dict[str, Any]:
    """Node 1: Calls the LLM with deterministic tools bound and automatic multi-provider fallback."""
    messages = list(state["messages"])
    # Ensure system prompt is always at the head
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    candidates = get_candidate_models()
    if not candidates:
        raise RuntimeError("No operational LLM providers configured in settings.")

    errors: list[str] = []
    for idx, (name, llm_with_tools) in enumerate(candidates):
        try:
            logger.info("Invoking agent node with provider: '%s' (candidate %d of %d)...", name, idx + 1, len(candidates))
            response = llm_with_tools.invoke(messages)
            return {"messages": [response]}
        except Exception as exc:
            err_msg = str(exc)
            # If provider hit quota/rate limits, activate cooldown
            if any(term in err_msg.lower() for term in ["429", "resource_exhausted", "quota", "rate limit", "ratelimit"]):
                PROVIDER_COOLDOWNS[name] = time.time() + COOLDOWN_DURATION_SECONDS
                logger.info("Activated %ds cooldown for provider '%s' due to rate/quota limits.", int(COOLDOWN_DURATION_SECONDS), name)

            logger.warning(
                "LLM provider '%s' failed during agent invocation (%s). Attempting next fallback...",
                name,
                err_msg,
            )
            errors.append(f"{name}: {err_msg}")

    error_summary = " | ".join(errors)
    logger.error("All candidate LLM providers failed: %s", error_summary)
    raise RuntimeError(f"All LLM providers failed in fallback chain: {error_summary}")


def tools_node(state: AgentState) -> dict[str, Any]:
    """Node 2: Deterministically executes tool calls and logs results."""
    last_message = state["messages"][-1]
    tool_messages: list[ToolMessage] = []
    new_records: list[dict[str, Any]] = list(state.get("tool_records", []))
    new_sources: list[str] = list(state.get("sources", []))

    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        for tc in last_message.tool_calls:
            name = tc["name"]
            args = tc["args"]
            tool_id = tc["id"]
            logger.info("Executing tool: %s with args: %s", name, args)

            tool_fn = TOOL_MAP.get(name)
            if tool_fn:
                try:
                    result = tool_fn.invoke(args)
                except Exception as exc:
                    logger.error("Tool execution failed for %s: %s", name, str(exc), exc_info=True)
                    result = {
                        "error": str(exc),
                        "value": None,
                        "unit": "error",
                        "interpretation": f"Execution of {name} failed: {str(exc)}",
                    }
            else:
                result = {
                    "error": f"Tool '{name}' is not recognized.",
                    "value": None,
                    "unit": "error",
                    "interpretation": f"Unknown tool: {name}",
                }

            # Extract RAG sources if applicable
            if name == "search_financial_docs" and isinstance(result, dict):
                docs = result.get("value", [])
                for d in docs:
                    src = d.get("source")
                    if src and src not in new_sources:
                        new_sources.append(src)

            new_records.append({
                "name": name,
                "args": args,
                "result": result,
            })

            tool_messages.append(
                ToolMessage(
                    content=json.dumps(result, default=str),
                    tool_call_id=tool_id,
                    name=name,
                )
            )

    return {
        "messages": tool_messages,
        "tool_records": new_records,
        "sources": new_sources,
    }


def should_continue(state: AgentState) -> Literal["tools", "__end__"]:
    """Conditional edge: Route to tools if tool_calls are requested, else END."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "__end__"


def create_risk_advisor_graph():
    """Build and compile the LangGraph ReAct workflow."""
    workflow = StateGraph(AgentState)

    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", tools_node)

    workflow.set_entry_point("agent")

    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "__end__": END,
        },
    )

    workflow.add_edge("tools", "agent")

    return workflow.compile()


risk_advisor_graph = create_risk_advisor_graph()


def run_agent(message: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    """Execute a complete conversational turn through the risk advisor graph.

    Args:
        message: The user's latest query.
        history: Prior conversation turns formatted as [{'role': 'user'|'assistant', 'content': '...'}].

    Returns:
        dict: Final synthesized response, list of tool calls executed, and document sources.
    """
    history_messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT)]

    if history:
        for turn in history:
            role = turn.get("role")
            content = turn.get("content", "")
            if role == "user":
                history_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                history_messages.append(AIMessage(content=content))

    history_messages.append(HumanMessage(content=message))

    initial_state: AgentState = {
        "messages": history_messages,
        "tool_records": [],
        "sources": [],
    }

    result = risk_advisor_graph.invoke(initial_state, {"recursion_limit": 20})

    final_message = result["messages"][-1]
    if isinstance(final_message, AIMessage):
        if isinstance(final_message.content, list):
            response_text = "".join(
                p.get("text", "") if isinstance(p, dict) else str(p)
                for p in final_message.content
            )
        else:
            response_text = str(final_message.content)
    else:
        response_text = str(final_message)

    return {
        "response": response_text,
        "tool_calls": result.get("tool_records", []),
        "sources": result.get("sources", []),
    }
