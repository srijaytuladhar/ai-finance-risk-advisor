"""LangGraph ReAct agent orchestration with deterministic tool binding."""

import json
import logging
from typing import Any, Literal
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph

from app.agent.prompts import SYSTEM_PROMPT
from app.agent.state import AgentState
from app.config import settings
from app.rag.retriever import search_financial_docs
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

# Complete suite of deterministic tools + RAG retriever tool
AGENT_TOOLS = [
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
    search_financial_docs,
]

TOOL_MAP = {t.name: t for t in AGENT_TOOLS}


def get_llm():
    """Instantiate the Chat model (Google Gemini, Hugging Face, or OpenAI) bound with deterministic tools."""
    if settings.GEMINI_API_KEY or "gemini" in settings.MODEL_NAME.lower():
        return ChatGoogleGenerativeAI(
            model=settings.MODEL_NAME,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.0,
        )
    if settings.HUGGINGFACE_API_KEY:
        return ChatOpenAI(
            base_url="https://router.huggingface.co/hf-inference/v1",
            api_key=settings.HUGGINGFACE_API_KEY,
            model=settings.MODEL_NAME if "/" in settings.MODEL_NAME else "meta-llama/Llama-3.3-70B-Instruct",
            temperature=0.0,
        )
    return ChatOpenAI(
        model=settings.MODEL_NAME,
        openai_api_key=settings.OPENAI_API_KEY,
        temperature=0.0,
        streaming=False,
    )


def agent_node(state: AgentState) -> dict[str, Any]:
    """Node 1: Calls the LLM with all deterministic tools bound."""
    llm = get_llm()
    llm_with_tools = llm.bind_tools(AGENT_TOOLS)

    messages = list(state["messages"])
    # Ensure system prompt is always at the head
    if not messages or not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = llm_with_tools.invoke(messages)
    return {"messages": [response]}


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
