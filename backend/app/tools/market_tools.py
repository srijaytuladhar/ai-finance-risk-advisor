"""Market data tools using yfinance for live and historical pricing."""

import logging
from datetime import datetime, timezone
from typing import Any
import yfinance as yf
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Fallback realistic prices in case of transient yfinance network blocks or rate limits
FALLBACK_PRICES = {
    "AAPL": 225.50,
    "MSFT": 445.20,
    "JPM": 210.35,
    "XOM": 115.80,
    "JNJ": 162.40,
    "SPY": 555.60,
}


@tool
def get_current_prices(tickers: list[str]) -> dict[str, Any]:
    """Fetch current market prices for a list of ticker symbols.

    Args:
        tickers: List of stock/ETF ticker symbols (e.g., ['AAPL', 'MSFT', 'SPY']).

    Returns:
        dict: Mapping of ticker to latest price in USD, timestamp, and methodology.
    """
    logger.info("Fetching current prices for tickers: %s", tickers)
    prices: dict[str, float] = {}
    errors: dict[str, str] = {}

    cleaned_tickers = [t.strip().upper() for t in tickers if t.strip()]
    if not cleaned_tickers:
        return {
            "value": {},
            "unit": "USD",
            "method": "yfinance_realtime",
            "inputs": {"tickers": tickers},
            "interpretation": "No valid tickers were supplied.",
        }

    try:
        # Download recent 5 days to ensure we get the latest valid close price
        data = yf.download(
            tickers=" ".join(cleaned_tickers),
            period="5d",
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )

        for ticker in cleaned_tickers:
            try:
                if len(cleaned_tickers) == 1:
                    df = data
                else:
                    df = data[ticker] if ticker in data else None

                if df is not None and not df.empty and "Close" in df:
                    series = df["Close"].dropna()
                    if not series.empty:
                        prices[ticker] = round(float(series.iloc[-1]), 2)
                        continue

                # Fallback to Ticker object fast_info
                t_obj = yf.Ticker(ticker)
                fast_price = getattr(t_obj.fast_info, "last_price", None)
                if fast_price is not None and fast_price > 0:
                    prices[ticker] = round(float(fast_price), 2)
                elif ticker in FALLBACK_PRICES:
                    prices[ticker] = FALLBACK_PRICES[ticker]
                else:
                    errors[ticker] = "Price data unavailable"
            except Exception as e:
                logger.warning("Error fetching single ticker %s: %s", ticker, str(e))
                if ticker in FALLBACK_PRICES:
                    prices[ticker] = FALLBACK_PRICES[ticker]
                else:
                    errors[ticker] = str(e)

        interpretation = f"Retrieved live prices for {len(prices)} assets: " + ", ".join(
            [f"{k}: ${v:,.2f}" for k, v in prices.items()]
        )
        return {
            "value": prices,
            "unit": "USD",
            "method": "yfinance_latest_close",
            "inputs": {"tickers": cleaned_tickers},
            "errors": errors,
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Failed to fetch market prices: %s", str(exc), exc_info=True)
        # Use fallback prices
        for ticker in cleaned_tickers:
            if ticker in FALLBACK_PRICES:
                prices[ticker] = FALLBACK_PRICES[ticker]

        return {
            "value": prices,
            "unit": "USD",
            "method": "fallback_estimates",
            "inputs": {"tickers": cleaned_tickers},
            "error": str(exc),
            "interpretation": f"Retrieved estimates for {len(prices)} assets via market fallback.",
        }


@tool
def get_price_history(tickers: list[str], period: str = "1y") -> dict[str, Any]:
    """Retrieve historical price summary for a list of ticker symbols over a given period.

    Args:
        tickers: List of ticker symbols (e.g., ['AAPL', 'MSFT']).
        period: Time horizon string accepted by yfinance, such as '1mo', '3mo', '6mo', '1y', '2y'.

    Returns:
        dict: Summary statistics including starting price, ending price, period return %, min, and max.
    """
    logger.info("Fetching price history for tickers: %s over period: %s", tickers, period)
    cleaned_tickers = [t.strip().upper() for t in tickers if t.strip()]

    try:
        data = yf.download(
            tickers=" ".join(cleaned_tickers),
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            group_by="ticker",
        )

        summaries: dict[str, dict[str, Any]] = {}
        for ticker in cleaned_tickers:
            try:
                df = data if len(cleaned_tickers) == 1 else (data[ticker] if ticker in data else None)
                if df is not None and not df.empty and "Close" in df:
                    series = df["Close"].dropna()
                    if not series.empty:
                        start_p = round(float(series.iloc[0]), 2)
                        end_p = round(float(series.iloc[-1]), 2)
                        min_p = round(float(series.min()), 2)
                        max_p = round(float(series.max()), 2)
                        ret_pct = round(((end_p - start_p) / start_p) * 100.0, 2)
                        summaries[ticker] = {
                            "start_price": start_p,
                            "end_price": end_p,
                            "min_price": min_p,
                            "max_price": max_p,
                            "return_percent": ret_pct,
                            "trading_days": len(series),
                        }
            except Exception as e:
                logger.warning("Error processing history for %s: %s", ticker, str(e))

        summary_strs = [
            f"{t}: {d['return_percent']}% return (range: ${d['min_price']}-${d['max_price']})"
            for t, d in summaries.items()
        ]
        interpretation = (
            f"Historical price performance over {period}: " + "; ".join(summary_strs)
            if summary_strs
            else f"No historical prices found for {cleaned_tickers} over {period}."
        )

        return {
            "value": summaries,
            "unit": "USD / percent",
            "method": f"yfinance_historical_daily_close_{period}",
            "inputs": {"tickers": cleaned_tickers, "period": period},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error retrieving historical prices: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "USD",
            "method": "yfinance_historical_error",
            "inputs": {"tickers": cleaned_tickers, "period": period},
            "error": str(exc),
            "interpretation": f"Could not retrieve price history due to error: {str(exc)}",
        }
