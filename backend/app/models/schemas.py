"""Pydantic schemas for request, response, and tool payloads."""

from typing import Any, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Represents a single message in the conversation history."""

    role: str = Field(description="Role of the author: 'user' or 'assistant'")
    content: str = Field(description="Textual content of the message")


class ChatRequest(BaseModel):
    """Incoming request payload for /api/chat."""

    message: str = Field(..., description="The user's query or instruction")
    history: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Prior conversation turns formatted as [{role, content}]",
    )


class ToolCallRecord(BaseModel):
    """Metadata regarding a tool call executed during agent reasoning."""

    name: str = Field(description="Name of the tool executed")
    args: dict[str, Any] = Field(default_factory=dict, description="Arguments passed to the tool")
    result: Any = Field(default=None, description="Returned result from the tool execution")


class ChatResponse(BaseModel):
    """Outgoing response payload from /api/chat."""

    response: str = Field(description="Synthesized markdown response from the assistant")
    tool_calls: list[ToolCallRecord] = Field(
        default_factory=list,
        description="Deterministic tools called to satisfy the request",
    )
    sources: list[str] = Field(
        default_factory=list,
        description="Document chunks or citations referenced during retrieval",
    )


class Holding(BaseModel):
    """Representation of an individual security holding in the portfolio."""

    ticker: str = Field(description="Ticker symbol of the asset")
    shares: float = Field(description="Quantity of shares owned")
    price: float = Field(default=0.0, description="Latest market price per share")
    value: float = Field(default=0.0, description="Total market value (shares * price)")
    weight: float = Field(default=0.0, description="Percentage weight in portfolio (0.0 to 1.0)")
    sector: str = Field(default="Unknown", description="Economic sector classification")


class PortfolioResponse(BaseModel):
    """Detailed response for /api/portfolio containing holdings, cash, and exposures."""

    holdings: list[Holding] = Field(default_factory=list, description="List of securities held")
    cash: float = Field(default=0.0, description="Cash reserves available")
    total_value: float = Field(default=0.0, description="Aggregate portfolio equity + cash")
    weights: dict[str, float] = Field(
        default_factory=dict,
        description="Asset weight breakdown by ticker and cash",
    )
    sectors: dict[str, float] = Field(
        default_factory=dict,
        description="Aggregate sector exposure percentages",
    )


class ToolResult(BaseModel):
    """Standardized deterministic tool output schema."""

    value: Any = Field(description="Calculated numerical value or structured output")
    unit: str = Field(description="Unit of measurement, e.g., 'percentage', 'ratio', 'USD'")
    method: str = Field(description="Calculation methodology utilized")
    inputs: dict[str, Any] = Field(description="Inputs supplied to the calculation")
    interpretation: str = Field(
        description="Plain-English sentence interpreting the result for the LLM"
    )
