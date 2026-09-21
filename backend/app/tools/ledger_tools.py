"""Deterministic financial calculation tools for analyzing personal ledger data (accounts, transactions, cash flow)."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from langchain_core.tools import tool

logger = logging.getLogger(__name__)

LEDGER_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "ledger.json"

_LEDGER_CACHE: dict[str, Any] = {}
_LAST_MODIFIED: float = 0.0


def get_raw_ledger() -> dict[str, Any]:
    """Load and cache ledger.json, auto-reloading if modified."""
    global _LEDGER_CACHE, _LAST_MODIFIED
    if not LEDGER_PATH.exists():
        logger.warning("ledger.json not found at %s", LEDGER_PATH)
        return {"accounts": [], "transactions": [], "categories": [], "contacts": []}

    try:
        mtime = LEDGER_PATH.stat().st_mtime
        if not _LEDGER_CACHE or mtime > _LAST_MODIFIED:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                _LEDGER_CACHE = json.load(f)
            _LAST_MODIFIED = mtime
            logger.info("Loaded ledger.json successfully (%d transactions)", len(_LEDGER_CACHE.get("transactions", [])))
        return _LEDGER_CACHE
    except Exception as exc:
        logger.error("Failed to read ledger.json: %s", str(exc), exc_info=True)
        return {"accounts": [], "transactions": [], "categories": [], "contacts": []}


def _get_account_map() -> dict[str, dict[str, Any]]:
    """Map account ID to account object."""
    ledger = get_raw_ledger()
    return {acc["id"]: acc for acc in ledger.get("accounts", []) if "id" in acc}


@tool
def get_account_balances() -> dict[str, Any]:
    """Retrieve the current balances, initial balances, and percentage share across all financial accounts.

    Accounts include Citizen Bank, eSewa, Cash, Laxmi Bank, and Prabhu Bank.

    Returns:
        dict: Detailed breakdown of each account's balance and the total liquid net worth in NPR.
    """
    logger.info("Executing get_account_balances")
    try:
        ledger = get_raw_ledger()
        accounts = ledger.get("accounts", [])
        total_balance = sum(float(acc.get("balance", 0.0)) for acc in accounts)

        accounts_detail = []
        for acc in accounts:
            bal = float(acc.get("balance", 0.0))
            weight = round(bal / total_balance, 4) if total_balance > 0 else 0.0
            accounts_detail.append({
                "id": acc.get("id"),
                "name": acc.get("name"),
                "type": acc.get("type"),
                "balance": round(bal, 2),
                "initial_balance": round(float(acc.get("initialBalance", 0.0)), 2),
                "weight": weight,
                "color": acc.get("color", "#6366f1"),
                "is_default": acc.get("isDefault", False),
            })

        # Sort accounts by balance descending
        accounts_detail.sort(key=lambda x: x["balance"], reverse=True)

        breakdown_str = ", ".join(
            [f"{a['name']}: Rs. {a['balance']:,.2f} ({a['weight']*100:.1f}%)" for a in accounts_detail]
        )
        interpretation = (
            f"Total liquid balance across {len(accounts)} accounts is Rs. {total_balance:,.2f}. "
            f"Breakdown: {breakdown_str}."
        )

        return {
            "value": {
                "total_balance": round(total_balance, 2),
                "account_count": len(accounts),
                "accounts": accounts_detail,
            },
            "unit": "NPR",
            "method": "deterministic_ledger_sum",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_account_balances: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "deterministic_ledger_sum",
            "inputs": {},
            "interpretation": f"Failed to retrieve account balances: {str(exc)}",
        }


@tool
def get_spending_summary(start_date: Optional[str] = None, end_date: Optional[str] = None) -> dict[str, Any]:
    """Calculate aggregate total income, total expenses, net savings, and savings rate.

    Args:
        start_date: Optional ISO date string (YYYY-MM-DD) to filter from.
        end_date: Optional ISO date string (YYYY-MM-DD) to filter to.

    Returns:
        dict: Overall cashflow statistics, total income, total expenses, net cash flow, and savings rate.
    """
    logger.info("Executing get_spending_summary (start_date=%s, end_date=%s)", start_date, end_date)
    try:
        ledger = get_raw_ledger()
        transactions = ledger.get("transactions", [])

        total_income = 0.0
        total_expense = 0.0
        total_transfer = 0.0
        tx_count = 0

        for t in transactions:
            t_date_str = t.get("date", "")
            if start_date and t_date_str < start_date:
                continue
            if end_date and t_date_str > end_date:
                continue

            tx_count += 1
            amt = float(t.get("amount", 0.0))
            t_type = t.get("type")
            if t_type == "Income":
                total_income += amt
            elif t_type == "Expense":
                total_expense += amt
            elif t_type == "Transfer":
                total_transfer += amt

        net_savings = total_income - total_expense
        savings_rate = (net_savings / total_income * 100.0) if total_income > 0 else 0.0

        time_frame = f"between {start_date} and {end_date}" if (start_date or end_date) else "all-time"
        interpretation = (
            f"Over {time_frame} across {tx_count:,} transactions: Total Income is Rs. {total_income:,.2f}, "
            f"Total Expenses are Rs. {total_expense:,.2f}, resulting in a net {'surplus' if net_savings >= 0 else 'deficit'} "
            f"of Rs. {abs(net_savings):,.2f} (Savings Rate: {savings_rate:.1f}%)."
        )

        return {
            "value": {
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "total_transfer": round(total_transfer, 2),
                "net_savings": round(net_savings, 2),
                "savings_rate_pct": round(savings_rate, 2),
                "transaction_count": tx_count,
            },
            "unit": "NPR and percentage",
            "method": "deterministic_cashflow_aggregation",
            "inputs": {"start_date": start_date, "end_date": end_date},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_spending_summary: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "deterministic_cashflow_aggregation",
            "inputs": {"start_date": start_date, "end_date": end_date},
            "interpretation": f"Failed to compute spending summary: {str(exc)}",
        }


@tool
def get_category_breakdown(
    transaction_type: str = "Expense",
    top_n: int = 10,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> dict[str, Any]:
    """Calculate spending or income categorized by category name, sorted by highest amount.

    Args:
        transaction_type: 'Expense' or 'Income' (default is 'Expense').
        top_n: Number of top categories to return (default 10).
        start_date: Optional filter start date (YYYY-MM-DD).
        end_date: Optional filter end date (YYYY-MM-DD).

    Returns:
        dict: Top categories with total amount, percentage share, and transaction count.
    """
    logger.info("Executing get_category_breakdown (type=%s, top_n=%d)", transaction_type, top_n)
    try:
        ledger = get_raw_ledger()
        transactions = ledger.get("transactions", [])
        categories_meta = {c["name"]: c for c in ledger.get("categories", []) if "name" in c}

        cat_amounts: dict[str, float] = {}
        cat_counts: dict[str, int] = {}
        total_type_amount = 0.0

        for t in transactions:
            if t.get("type") != transaction_type:
                continue
            t_date_str = t.get("date", "")
            if start_date and t_date_str < start_date:
                continue
            if end_date and t_date_str > end_date:
                continue

            amt = float(t.get("amount", 0.0))
            cat = t.get("category") or "Uncategorized"
            cat_amounts[cat] = cat_amounts.get(cat, 0.0) + amt
            cat_counts[cat] = cat_counts.get(cat, 0) + 1
            total_type_amount += amt

        sorted_cats = sorted(cat_amounts.items(), key=lambda x: x[1], reverse=True)
        top_cats = sorted_cats[:top_n]

        category_list = []
        for cat, amt in top_cats:
            pct = round(amt / total_type_amount, 4) if total_type_amount > 0 else 0.0
            meta = categories_meta.get(cat, {})
            category_list.append({
                "category": cat,
                "amount": round(amt, 2),
                "percentage": pct,
                "count": cat_counts.get(cat, 0),
                "color": meta.get("color"),
                "icon": meta.get("icon"),
            })

        top_summary_str = ", ".join(
            [f"{c['category']}: Rs. {c['amount']:,.2f} ({c['percentage']*100:.1f}%)" for c in category_list[:5]]
        )
        interpretation = (
            f"Top {len(category_list)} {transaction_type.lower()} categories out of Rs. {total_type_amount:,.2f} total: "
            f"{top_summary_str}."
        )

        return {
            "value": {
                "transaction_type": transaction_type,
                "total_amount": round(total_type_amount, 2),
                "top_categories": category_list,
                "all_categories_count": len(cat_amounts),
            },
            "unit": "NPR and ratio",
            "method": "category_aggregation",
            "inputs": {"transaction_type": transaction_type, "top_n": top_n},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_category_breakdown: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "category_aggregation",
            "inputs": {"transaction_type": transaction_type, "top_n": top_n},
            "interpretation": f"Failed to compute category breakdown: {str(exc)}",
        }


@tool
def query_ledger_transactions(
    query: Optional[str] = None,
    category: Optional[str] = None,
    account_name: Optional[str] = None,
    transaction_type: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    limit: int = 15,
) -> dict[str, Any]:
    """Search and filter transactions from the ledger matching specific criteria.

    Args:
        query: Substring search term in description, category, or note.
        category: Exact or case-insensitive category name (e.g., 'Renovation', 'Bike', 'Manang', 'Chiya').
        account_name: Name of the account (e.g., 'Citizen Bank', 'eSewa', 'Cash').
        transaction_type: 'Income', 'Expense', or 'Transfer'.
        min_amount: Minimum transaction amount filter.
        max_amount: Maximum transaction amount filter.
        limit: Max transactions to return (default 15).

    Returns:
        dict: Matching transactions with date, amount, description, category, and account.
    """
    logger.info("Executing query_ledger_transactions (query=%s, category=%s, limit=%d)", query, category, limit)
    try:
        ledger = get_raw_ledger()
        transactions = ledger.get("transactions", [])
        account_map = _get_account_map()

        q_lower = query.lower() if query else None
        cat_lower = category.lower() if category else None
        acc_lower = account_name.lower() if account_name else None
        t_type_lower = transaction_type.lower() if transaction_type else None

        matches = []
        for t in transactions:
            t_acc = account_map.get(t.get("accountId", ""), {})
            t_acc_name = t_acc.get("name", "Unknown Account")
            t_cat = t.get("category") or ""
            t_desc = t.get("description") or ""
            t_type = t.get("type") or ""
            amt = float(t.get("amount", 0.0))

            if t_type_lower and t_type.lower() != t_type_lower:
                continue
            if cat_lower and cat_lower not in t_cat.lower():
                continue
            if acc_lower and acc_lower not in t_acc_name.lower():
                continue
            if min_amount is not None and amt < min_amount:
                continue
            if max_amount is not None and amt > max_amount:
                continue
            if q_lower:
                if q_lower not in t_desc.lower() and q_lower not in t_cat.lower() and q_lower not in t_acc_name.lower():
                    continue

            matches.append({
                "id": t.get("id"),
                "date": t.get("date", "")[:10],
                "time": t.get("date", "")[11:19],
                "type": t_type,
                "amount": amt,
                "description": t_desc,
                "category": t_cat,
                "account": t_acc_name,
            })

        # Sort by date descending
        matches.sort(key=lambda x: x["date"], reverse=True)
        total_matched = len(matches)
        total_matched_amt = sum(m["amount"] for m in matches)
        returned_matches = matches[:limit]

        interpretation = (
            f"Found {total_matched} transactions matching criteria totaling Rs. {total_matched_amt:,.2f}. "
            f"Returning the most recent {len(returned_matches)}."
        )

        return {
            "value": {
                "total_matched": total_matched,
                "total_matched_amount": round(total_matched_amt, 2),
                "transactions": returned_matches,
            },
            "unit": "transactions",
            "method": "deterministic_ledger_filter",
            "inputs": {"query": query, "category": category, "account": account_name, "type": transaction_type},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in query_ledger_transactions: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "deterministic_ledger_filter",
            "inputs": {},
            "interpretation": f"Failed to filter transactions: {str(exc)}",
        }


@tool
def get_monthly_cashflow() -> dict[str, Any]:
    """Calculate monthly aggregated income, expenses, and net cash flow across the entire ledger timeline.

    Returns:
        dict: Month-by-month cashflow progression (YYYY-MM).
    """
    logger.info("Executing get_monthly_cashflow")
    try:
        ledger = get_raw_ledger()
        transactions = ledger.get("transactions", [])

        monthly_data: dict[str, dict[str, float]] = {}
        for t in transactions:
            d_str = t.get("date", "")
            if not d_str or len(d_str) < 7:
                continue
            month_key = d_str[:7]  # YYYY-MM
            if month_key not in monthly_data:
                monthly_data[month_key] = {"income": 0.0, "expense": 0.0, "transfer": 0.0}

            amt = float(t.get("amount", 0.0))
            ttype = t.get("type")
            if ttype == "Income":
                monthly_data[month_key]["income"] += amt
            elif ttype == "Expense":
                monthly_data[month_key]["expense"] += amt
            elif ttype == "Transfer":
                monthly_data[month_key]["transfer"] += amt

        # Sort months chronologically
        sorted_months = sorted(monthly_data.keys())
        cashflow_list = []
        for m in sorted_months:
            inc = round(monthly_data[m]["income"], 2)
            exp = round(monthly_data[m]["expense"], 2)
            net = round(inc - exp, 2)
            cashflow_list.append({
                "month": m,
                "income": inc,
                "expense": exp,
                "net": net,
            })

        latest_3 = cashflow_list[-3:] if len(cashflow_list) >= 3 else cashflow_list
        latest_summary = "; ".join([f"{m['month']} (Inc: Rs. {m['income']:,.0f}, Exp: Rs. {m['expense']:,.0f}, Net: Rs. {m['net']:,.0f})" for m in latest_3])
        interpretation = f"Analyzed {len(cashflow_list)} active months. Recent trajectory: {latest_summary}."

        return {
            "value": {
                "months_count": len(cashflow_list),
                "monthly_cashflow": cashflow_list,
            },
            "unit": "NPR per month",
            "method": "monthly_aggregation",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in get_monthly_cashflow: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "monthly_aggregation",
            "inputs": {},
            "interpretation": f"Failed to compute monthly cash flow: {str(exc)}",
        }


@tool
def calculate_financial_health_metrics() -> dict[str, Any]:
    """Calculate core financial health indicators: emergency runway, average monthly burn, and savings rate.

    Returns:
        dict: Liquid reserves, average monthly expense, runway in months, and risk diagnostics.
    """
    logger.info("Executing calculate_financial_health_metrics")
    try:
        balances_res = get_account_balances.invoke({})
        total_liquid = balances_res.get("value", {}).get("total_balance", 0.0)

        cashflow_res = get_monthly_cashflow.invoke({})
        monthly = cashflow_res.get("value", {}).get("monthly_cashflow", [])

        if not monthly:
            return {
                "value": {"runway_months": 0.0, "total_liquid": total_liquid},
                "unit": "metrics",
                "method": "runway_diagnostics",
                "inputs": {},
                "interpretation": "Insufficient monthly data to compute runway.",
            }

        # Calculate average monthly expenses (exclude current partial month if minimal, or average all)
        total_exp = sum(m["expense"] for m in monthly)
        avg_monthly_exp = total_exp / len(monthly) if monthly else 1.0

        runway_months = round(total_liquid / avg_monthly_exp, 2) if avg_monthly_exp > 0 else 0.0

        # Overall savings rate
        total_inc = sum(m["income"] for m in monthly)
        overall_savings_rate = round(((total_inc - total_exp) / total_inc * 100), 2) if total_inc > 0 else 0.0

        interpretation = (
            f"Current liquid funds of Rs. {total_liquid:,.2f} provide approximately {runway_months:.1f} months of emergency runway "
            f"based on an average monthly burn rate of Rs. {avg_monthly_exp:,.2f}. Overall net savings rate is {overall_savings_rate:.1f}%."
        )

        return {
            "value": {
                "total_liquid_reserves": round(total_liquid, 2),
                "average_monthly_expense": round(avg_monthly_exp, 2),
                "emergency_runway_months": runway_months,
                "overall_savings_rate_pct": overall_savings_rate,
                "months_evaluated": len(monthly),
            },
            "unit": "months and NPR",
            "method": "runway_diagnostics",
            "inputs": {},
            "interpretation": interpretation,
        }
    except Exception as exc:
        logger.error("Error in calculate_financial_health_metrics: %s", str(exc), exc_info=True)
        return {
            "value": {},
            "unit": "error",
            "method": "runway_diagnostics",
            "inputs": {},
            "interpretation": f"Failed to calculate financial health metrics: {str(exc)}",
        }
