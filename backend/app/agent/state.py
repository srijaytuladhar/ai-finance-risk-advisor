"""Agent state definition for the LangGraph workflow."""

from typing import Annotated, Any, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """The runtime state tracking messages, tool execution history, and citation sources."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_records: list[dict[str, Any]]
    sources: list[str]
