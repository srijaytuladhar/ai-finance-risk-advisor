package com.fonepay.riskadvisor.tools;

import com.fonepay.riskadvisor.dto.ToolResult;
import com.fonepay.riskadvisor.service.DocumentRetrievalService;
import com.fonepay.riskadvisor.service.LedgerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Component
public class LedgerTools {
    private static final Logger logger = LoggerFactory.getLogger(LedgerTools.class);

    private final LedgerService ledgerService;
    private final DocumentRetrievalService retrievalService;
    private final ToolExecutionTracker tracker;

    public LedgerTools(LedgerService ledgerService, DocumentRetrievalService retrievalService, ToolExecutionTracker tracker) {
        this.ledgerService = ledgerService;
        this.retrievalService = retrievalService;
        this.tracker = tracker;
    }

    @Tool(name = "get_account_balances", description = "Retrieve current balances, initial balances, and percentage share across all financial accounts (Citizen Bank, eSewa, Cash, Laxmi Bank, Prabhu Bank) in NPR.")
    public ToolResult get_account_balances() {
        logger.info("Tool called: get_account_balances");
        ToolResult result = ledgerService.getAccountBalances();
        tracker.record("get_account_balances", Map.of(), result);
        return result;
    }

    @Tool(name = "get_spending_summary", description = "Calculate aggregate total income, total expenses, net savings, and savings rate. Supports optional start_date and end_date (YYYY-MM-DD).")
    public ToolResult get_spending_summary(
            @ToolParam(description = "Optional start date in YYYY-MM-DD", required = false) String start_date,
            @ToolParam(description = "Optional end date in YYYY-MM-DD", required = false) String end_date) {
        logger.info("Tool called: get_spending_summary (start_date={}, end_date={})", start_date, end_date);
        ToolResult result = ledgerService.getSpendingSummary(start_date, end_date);
        Map<String, Object> args = new HashMap<>();
        if (start_date != null) args.put("start_date", start_date);
        if (end_date != null) args.put("end_date", end_date);
        tracker.record("get_spending_summary", args, result);
        return result;
    }

    @Tool(name = "get_category_breakdown", description = "Calculate spending or income categorized by category name, sorted by highest amount. Supports transaction_type ('Expense' or 'Income'), top_n, and date filters.")
    public ToolResult get_category_breakdown(
            @ToolParam(description = "Transaction type: 'Expense' or 'Income' (default Expense)", required = false) String transaction_type,
            @ToolParam(description = "Number of top categories to return (default 10)", required = false) Integer top_n,
            @ToolParam(description = "Optional filter start date (YYYY-MM-DD)", required = false) String start_date,
            @ToolParam(description = "Optional filter end date (YYYY-MM-DD)", required = false) String end_date) {
        logger.info("Tool called: get_category_breakdown (type={}, top_n={})", transaction_type, top_n);
        ToolResult result = ledgerService.getCategoryBreakdown(transaction_type, top_n, start_date, end_date);
        Map<String, Object> args = new HashMap<>();
        if (transaction_type != null) args.put("transaction_type", transaction_type);
        if (top_n != null) args.put("top_n", top_n);
        if (start_date != null) args.put("start_date", start_date);
        if (end_date != null) args.put("end_date", end_date);
        tracker.record("get_category_breakdown", args, result);
        return result;
    }

    @Tool(name = "query_ledger_transactions", description = "Search and filter transactions from the ledger matching search query, category, account name, type, or amount bounds.")
    public ToolResult query_ledger_transactions(
            @ToolParam(description = "Keyword query in description, category, or note", required = false) String query,
            @ToolParam(description = "Exact or partial category name (e.g. Renovation, Bike, Manang, Chiya)", required = false) String category,
            @ToolParam(description = "Account name (e.g. Citizen Bank, eSewa, Cash)", required = false) String account_name,
            @ToolParam(description = "Transaction type: 'Income', 'Expense', or 'Transfer'", required = false) String transaction_type,
            @ToolParam(description = "Minimum amount in NPR", required = false) Double min_amount,
            @ToolParam(description = "Maximum amount in NPR", required = false) Double max_amount,
            @ToolParam(description = "Max transactions to return (default 15)", required = false) Integer limit) {
        logger.info("Tool called: query_ledger_transactions (query={}, category={}, limit={})", query, category, limit);
        ToolResult result = ledgerService.queryLedgerTransactions(query, category, account_name, transaction_type, min_amount, max_amount, limit);
        Map<String, Object> args = new HashMap<>();
        if (query != null) args.put("query", query);
        if (category != null) args.put("category", category);
        if (account_name != null) args.put("account_name", account_name);
        if (transaction_type != null) args.put("transaction_type", transaction_type);
        if (min_amount != null) args.put("min_amount", min_amount);
        if (max_amount != null) args.put("max_amount", max_amount);
        if (limit != null) args.put("limit", limit);
        tracker.record("query_ledger_transactions", args, result);
        return result;
    }

    @Tool(name = "get_monthly_cashflow", description = "Calculate monthly aggregated income, expenses, and net cash flow across the entire ledger timeline (YYYY-MM).")
    public ToolResult get_monthly_cashflow() {
        logger.info("Tool called: get_monthly_cashflow");
        ToolResult result = ledgerService.getMonthlyCashflow();
        tracker.record("get_monthly_cashflow", Map.of(), result);
        return result;
    }

    @Tool(name = "calculate_financial_health_metrics", description = "Calculate core financial health indicators: emergency runway (in months), average monthly burn rate, and overall savings rate.")
    public ToolResult calculate_financial_health_metrics() {
        logger.info("Tool called: calculate_financial_health_metrics");
        ToolResult result = ledgerService.calculateFinancialHealthMetrics();
        tracker.record("calculate_financial_health_metrics", Map.of(), result);
        return result;
    }

    @Tool(name = "search_ledger_docs", description = "Search indexed personal financial ledger records, trip expenses (e.g. Manang vacation), vehicle maintenance (Bike servicing), contacts (Dad, Roslina), and lifestyle spending notes.")
    public ToolResult search_ledger_docs(
            @ToolParam(description = "Search query relating to ledger transactions, trips, or spending notes", required = true) String query) {
        logger.info("Tool called: search_ledger_docs (query={})", query);
        ToolResult result = retrievalService.searchDocs(query);
        tracker.record("search_ledger_docs", Map.of("query", query), result);
        tracker.addSource("ledger.json");
        return result;
    }

    @Tool(name = "search_financial_docs", description = "Search authoritative financial documentation, risk glossary definitions, and ledger investment policy guidelines.")
    public ToolResult search_financial_docs(
            @ToolParam(description = "Search question or keywords relating to financial risk concepts or guidelines", required = true) String query) {
        logger.info("Tool called: search_financial_docs (query={})", query);
        ToolResult result = retrievalService.searchDocs(query);
        tracker.record("search_financial_docs", Map.of("query", query), result);
        tracker.addSource("investment_policy.md");
        tracker.addSource("risk_glossary.md");
        return result;
    }
}
