"""Portfolio management tools for holdings inspection, weights, sector exposure, and rebalancing."""

import json
import logging
from pathlib import Path
from typing import Any
import yfinance as yf
from langchain_core.tools import tool

from app.tools.market_tools import FALLBACK_PRICES, get_current_prices

logger = logging.getLogger(__name__)

PORTFOLIO_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "portfolio.json"

STATIC_SECTOR_MAP = {
    "AAPL": "Information Technology",
    "MSFT": "Information Technology",
    "JPM": "Financial Services",
    "XOM": "Energy",
    "JNJ": "Healthcare",
    "SPY": "Broad Market Index",
}


def _read_raw_portfolio() -> dict[str, Any]:
    """Read portfolio JSON from disk or return a standard default."""
    if PORTFOLIO_PATH.exists():
        try:
            with open(PORTFOLIO_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to read portfolio.json: %s", str(e))
    return {
        "holdings": [
            {"ticker": "AAPL", "shares": 50},
            {"ticker": "MSFT", "shares": 30},
            {"ticker": "JPM", "shares": 40},
            {"ticker": "XOM", "shares": 25},
            {"ticker": "JNJ", "shares": 35},
            {"ticker": "SPY", "shares": 20},
        ],
        "cash": 15000.0,
    }


def _get_prices_for_portfolio(tickers: list[str]) -> dict[str, float]:
    """Internal helper to retrieve prices for a set of tickers with fallback resilience."""
    price_res = get_current_prices.invoke({"tickers": tickers})
    prices: dict[str, float] = price_res.get("value", {})
    for t in tickers:
        if t not in prices or prices[t] <= 0:
            prices[t] = FALLBACK_PRICES.get(t, 100.0)
    return prices


@tool
def get_portfolio_holdings() -> dict[str, Any]:
    """Retrieve the raw portfolio holdings, share counts, and uninvested cash reserves.

    Returns:
        dict: Raw holdings list and cash balance.
    """
    logger.info("Executing get_portfolio_holdings")
    try:
        data = _read_raw_portfolio()
        holdings = data.get("holdings", [])
        cash = float(data.get("cash", 0.0))

        tickers_held = [h["ticker"] for h in holdings]
        interpretation = (
            f"The portfolio holds {len(holdings)} distinct assets: {', '.join(tickers_held)}, "
            f"with ${cash:,.2f} held in uninvested cash reserves."
        )

        return {
            "value": {"holdings": holdings, "cash": cash},
            "unit": "shares and USD",
            "method": "file_read_portfolio_json",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_portfolio_holdings: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "file_read_portfolio_json",
            "inputs": {},
            "interpretation": f"Failed to retrieve portfolio holdings: {str(exc)}",
        }


@tool
def calculate_weights() -> dict[str, Any]:
    """Calculate the current market values and percentage weights for each holding and cash.

    Returns:
        dict: Detailed breakdown of current price, market value, and percentage weight per asset.
    """
    logger.info("Executing calculate_weights")
    try:
        data = _read_raw_portfolio()
        holdings = data.get("holdings", [])
        cash = float(data.get("cash", 0.0))

        tickers = [h["ticker"] for h in holdings]
        prices = _get_prices_for_portfolio(tickers)

        holdings_detail = []
        equity_value = 0.0

        for h in holdings:
            t = h["ticker"]
            shares = float(h["shares"])
            price = prices.get(t, 0.0)
            mkt_val = round(shares * price, 2)
            equity_value += mkt_val
            holdings_detail.append({
                "ticker": t,
                "shares": shares,
                "price": price,
                "value": mkt_val,
            })

        total_portfolio_value = round(equity_value + cash, 2)
        weights: dict[str, float] = {}

        for hd in holdings_detail:
            w = round(hd["value"] / total_portfolio_value, 4) if total_portfolio_value > 0 else 0.0
            hd["weight"] = w
            weights[hd["ticker"]] = w

        cash_weight = round(cash / total_portfolio_value, 4) if total_portfolio_value > 0 else 0.0
        weights["CASH"] = cash_weight

        top_asset = max(weights.items(), key=lambda x: x[1]) if weights else ("None", 0)

        interpretation = (
            f"Total portfolio value is ${total_portfolio_value:,.2f} (${equity_value:,.2f} equities + "
            f"${cash:,.2f} cash). Largest position is {top_asset[0]} at {top_asset[1]*100:.1f}% weight."
        )

        return {
            "value": {
                "total_value": total_portfolio_value,
                "equity_value": round(equity_value, 2),
                "cash": cash,
                "weights": weights,
                "holdings_detail": holdings_detail,
            },
            "unit": "ratio and USD",
            "method": "live_price_valuation",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in calculate_weights: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "live_price_valuation",
            "inputs": {},
            "interpretation": f"Failed to calculate weights: {str(exc)}",
        }


@tool
def get_sector_exposure() -> dict[str, Any]:
    """Calculate aggregate portfolio exposure categorized by economic sector.

    Returns:
        dict: Sector exposure breakdown with dollar value and percentage weights.
    """
    logger.info("Executing get_sector_exposure")
    try:
        weights_data = calculate_weights.invoke({})
        val = weights_data.get("value", {})
        holdings_detail = val.get("holdings_detail", [])
        cash = val.get("cash", 0.0)
        total_val = val.get("total_value", 1.0)

        sector_values: dict[str, float] = {}

        for h in holdings_detail:
            ticker = h["ticker"]
            sector = STATIC_SECTOR_MAP.get(ticker)
            if not sector:
                try:
                    t_obj = yf.Ticker(ticker)
                    sector = t_obj.info.get("sector", "Other Equities")
                except Exception:
                    sector = "Other Equities"

            h["sector"] = sector
            sector_values[sector] = sector_values.get(sector, 0.0) + h["value"]

        if cash > 0:
            sector_values["Cash & Reserves"] = sector_values.get("Cash & Reserves", 0.0) + cash

        sector_weights: dict[str, float] = {
            sec: round(amt / total_val, 4) for sec, amt in sector_values.items()
        }

        # Identify top sector
        sorted_sectors = sorted(sector_weights.items(), key=lambda x: x[1], reverse=True)
        top_sec, top_pct = sorted_sectors[0] if sorted_sectors else ("None", 0.0)

        interpretation = (
            f"Largest sector exposure is {top_sec} at {top_pct*100:.1f}%. "
            f"Complete exposure: " + ", ".join([f"{k}: {v*100:.1f}%" for k, v in sorted_sectors])
        )

        return {
            "value": {
                "sector_weights": sector_weights,
                "sector_values": {k: round(v, 2) for k, v in sector_values.items()},
            },
            "unit": "percentage / ratio",
            "method": "sector_aggregation",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_sector_exposure: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "sector_aggregation",
            "inputs": {},
            "interpretation": f"Failed to compute sector exposures: {str(exc)}",
        }


@tool
def suggest_rebalance(target_weights: dict[str, float]) -> dict[str, Any]:
    """Compare current portfolio weights against target weights and generate actionable trade orders.

    Args:
        target_weights: Dictionary mapping ticker symbols (or 'CASH') to target percentage weights
                        (e.g., {'AAPL': 0.20, 'MSFT': 0.20, 'JPM': 0.15, 'XOM': 0.10, 'JNJ': 0.15, 'SPY': 0.10, 'CASH': 0.10}).

    Returns:
        dict: Detailed rebalancing instructions with dollar adjustments and share buy/sell quantities.
    """
    logger.info("Executing suggest_rebalance with target_weights: %s", target_weights)
    try:
        weights_data = calculate_weights.invoke({})
        val = weights_data.get("value", {})
        total_val = val.get("total_value", 0.0)
        holdings_detail = val.get("holdings_detail", [])
        current_weights = val.get("weights", {})
        cash = val.get("cash", 0.0)

        current_prices = {h["ticker"]: h["price"] for h in holdings_detail}
        current_shares = {h["ticker"]: h["shares"] for h in holdings_detail}

        # Normalize target weights if given as whole numbers (e.g., 20 instead of 0.20)
        sum_targets = sum(target_weights.values())
        norm_targets: dict[str, float] = {}
        for k, v in target_weights.items():
            norm_targets[k.upper()] = (v / 100.0) if sum_targets > 1.5 else v

        trades = []
        drift_warnings = []

        all_keys = set(list(current_weights.keys()) + list(norm_targets.keys()))

        for asset in all_keys:
            if asset == "CASH":
                curr_w = current_weights.get("CASH", 0.0)
                tgt_w = norm_targets.get("CASH", 0.15)
                drift = round(curr_w - tgt_w, 4)
                target_cash = round(total_val * tgt_w, 2)
                cash_delta = round(target_cash - cash, 2)
                trades.append({
                    "ticker": "CASH",
                    "action": "DEPOSIT" if cash_delta > 0 else "WITHDRAW/DEPLOY",
                    "current_weight": curr_w,
                    "target_weight": tgt_w,
                    "drift_percent": round(drift * 100, 2),
                    "target_shares": 0,
                    "shares_to_trade": 0,
                    "dollar_amount": abs(cash_delta),
                })
                continue

            curr_w = current_weights.get(asset, 0.0)
            tgt_w = norm_targets.get(asset, 0.0)
            drift = round(curr_w - tgt_w, 4)

            curr_shares = current_shares.get(asset, 0.0)
            price = current_prices.get(asset, FALLBACK_PRICES.get(asset, 100.0))

            target_dollar = total_val * tgt_w
            target_shares = round(target_dollar / price, 2) if price > 0 else 0.0
            shares_to_trade = round(target_shares - curr_shares, 2)
            dollar_amount = round(abs(shares_to_trade * price), 2)

            action = "HOLD"
            if shares_to_trade > 0.5:
                action = "BUY"
            elif shares_to_trade < -0.5:
                action = "SELL"

            if abs(drift) > 0.05:
                drift_warnings.append(f"{asset} drifted by {drift*100:+.1f}%")

            trades.append({
                "ticker": asset,
                "action": action,
                "current_weight": curr_w,
                "target_weight": tgt_w,
                "drift_percent": round(drift * 100, 2),
                "shares_to_trade": abs(shares_to_trade),
                "target_shares": target_shares,
                "dollar_amount": dollar_amount,
            })

        interpretation = (
            f"Rebalancing plan generated for {len(trades)} assets across total portfolio of ${total_val:,.2f}. "
            f"Key drifts noted: {', '.join(drift_warnings) if drift_warnings else 'All positions within normal drift bands.'}"
        )

        return {
            "value": {
                "trades": trades,
                "total_portfolio_value": total_val,
                "drift_warnings": drift_warnings,
            },
            "unit": "shares and USD",
            "method": "proportional_target_drift_rebalancing",
            "inputs": {"target_weights": target_weights},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in suggest_rebalance: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "proportional_target_drift_rebalancing",
            "inputs": {"target_weights": target_weights},
            "interpretation": f"Failed to generate rebalancing plan: {str(exc)}",
        }
