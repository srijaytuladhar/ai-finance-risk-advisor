"""Tools module initialization exposing deterministic calculation and market tools."""

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

ALL_TOOLS = [
    get_current_prices,
    get_price_history,
    get_portfolio_holdings,
    calculate_weights,
    get_sector_exposure,
    suggest_rebalance,
    calculate_var,
    calculate_sharpe,
    calculate_max_drawdown,
    calculate_volatility,
    calculate_beta,
]

__all__ = [
    "ALL_TOOLS",
    "get_current_prices",
    "get_price_history",
    "get_portfolio_holdings",
    "calculate_weights",
    "get_sector_exposure",
    "suggest_rebalance",
    "calculate_var",
    "calculate_sharpe",
    "calculate_max_drawdown",
    "calculate_volatility",
    "calculate_beta",
]
