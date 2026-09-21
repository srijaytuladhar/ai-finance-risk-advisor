"""Pydantic schemas for request, response, tool payloads, and ledger analytics."""

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
    """Representation of an individual asset holding."""

    ticker: str = Field(description="Identifier or ticker symbol of the asset")
    shares: float = Field(default=0.0, description="Quantity of shares or units")
    price: float = Field(default=0.0, description="Latest market price per unit")
    value: float = Field(default=0.0, description="Total valuation in NPR")
    weight: float = Field(default=0.0, description="Percentage weight in total liquid funds (0.0 to 1.0)")
    sector: str = Field(default="Banking", description="Sector or category classification")


class AccountItem(BaseModel):
    """Individual financial account representation."""

    id: str = Field(description="Account unique ID")
    name: str = Field(description="Account name (e.g., Citizen Bank, eSewa, Cash)")
    type: str = Field(description="Account type: 'Bank', 'Wallet', or 'Cash'")
    balance: float = Field(description="Current balance in NPR")
    initial_balance: float = Field(default=0.0, description="Initial starting balance")
    weight: float = Field(default=0.0, description="Share of total liquid balance")
    color: str = Field(default="#6366f1", description="UI hex display color")
    is_default: bool = Field(default=False, description="Default transaction account flag")


class CategorySummary(BaseModel):
    """Spending or income aggregated by category."""

    category: str = Field(description="Category name")
    amount: float = Field(description="Total amount spent or earned in NPR")
    percentage: float = Field(description="Percentage share of total expenses or income")
    count: int = Field(default=0, description="Number of transactions")
    color: Optional[str] = Field(default=None, description="Category display color")
    icon: Optional[str] = Field(default=None, description="Category icon identifier")


class TransactionRecord(BaseModel):
    """Individual transaction record."""

    id: str = Field(description="Transaction ID")
    date: str = Field(description="Transaction date (YYYY-MM-DD)")
    type: str = Field(description="'Income', 'Expense', or 'Transfer'")
    amount: float = Field(description="Transaction amount in NPR")
    description: str = Field(default="", description="Description or note")
    category: str = Field(default="", description="Category classification")
    account_name: str = Field(default="", description="Account associated with transaction")


class MonthlyCashflow(BaseModel):
    """Monthly cashflow summary entry."""

    month: str = Field(description="Month string (YYYY-MM)")
    income: float = Field(description="Total income for the month")
    expense: float = Field(description="Total expense for the month")
    net: float = Field(description="Net cashflow (income - expense)")


class PortfolioResponse(BaseModel):
    """Unified financial analytics response containing accounts, categories, and cashflow."""

    # Top-level ledger metrics
    total_balance: float = Field(default=0.0, description="Total liquid funds across all accounts in NPR")
    total_income: float = Field(default=0.0, description="Total lifetime income in NPR")
    total_expense: float = Field(default=0.0, description="Total lifetime expenses in NPR")
    net_cashflow: float = Field(default=0.0, description="Net savings or deficit in NPR")
    savings_rate: float = Field(default=0.0, description="Net savings rate percentage")
    transaction_count: int = Field(default=0, description="Total recorded transactions")

    # Structured collections
    accounts: list[AccountItem] = Field(default_factory=list, description="Account list with balances and shares")
    top_categories: list[CategorySummary] = Field(default_factory=list, description="Top spending categories")
    monthly_cashflow: list[MonthlyCashflow] = Field(default_factory=list, description="Month-by-month cashflow history")
    recent_transactions: list[TransactionRecord] = Field(default_factory=list, description="Most recent transactions")

    # Backwards compatibility fields for older components
    holdings: list[Holding] = Field(default_factory=list, description="List of securities or accounts as holdings")
    cash: float = Field(default=0.0, description="Cash reserves available")
    total_value: float = Field(default=0.0, description="Aggregate portfolio equity + cash")
    weights: dict[str, float] = Field(default_factory=dict, description="Asset weight breakdown")
    sectors: dict[str, float] = Field(default_factory=dict, description="Category exposure percentages")


class ToolResult(BaseModel):
    """Standardized deterministic tool output schema."""

    value: Any = Field(description="Calculated numerical value or structured output")
    unit: str = Field(description="Unit of measurement")
    method: str = Field(description="Calculation methodology utilized")
    inputs: dict[str, Any] = Field(description="Inputs supplied to the calculation")
    interpretation: str = Field(description="Plain-English sentence interpreting the result for the LLM")
