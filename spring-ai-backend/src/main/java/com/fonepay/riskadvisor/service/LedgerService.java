package com.fonepay.riskadvisor.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fonepay.riskadvisor.dto.*;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.ClassPathResource;
import org.springframework.stereotype.Service;

import java.io.File;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.DecimalFormat;
import java.util.*;
import java.util.stream.Collectors;

@Service
public class LedgerService {
    private static final Logger logger = LoggerFactory.getLogger(LedgerService.class);
    private static final DecimalFormat CURRENCY_FMT = new DecimalFormat("#,##0.00");

    private final ObjectMapper objectMapper;

    private JsonNode rawLedger;
    private final Map<String, JsonNode> accountMap = new HashMap<>();
    private final Map<String, JsonNode> categoryMap = new HashMap<>();
    private final List<JsonNode> transactionList = new ArrayList<>();
    private final List<JsonNode> rawAccountList = new ArrayList<>();

    public LedgerService() {
        this.objectMapper = new ObjectMapper();
    }

    public LedgerService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper != null ? objectMapper : new ObjectMapper();
    }

    @PostConstruct
    public synchronized void init() {
        loadLedger();
    }

    public synchronized void loadLedger() {
        try {
            InputStream is = null;
            ClassPathResource cpr = new ClassPathResource("data/ledger.json");
            if (cpr.exists()) {
                is = cpr.getInputStream();
                logger.info("Loaded ledger.json from classpath data/ledger.json");
            } else {
                Path localPath = Path.of("src/main/resources/data/ledger.json");
                if (Files.exists(localPath)) {
                    is = Files.newInputStream(localPath);
                    logger.info("Loaded ledger.json from src/main/resources/data/ledger.json");
                } else {
                    Path backendPath = Path.of("../backend/data/ledger.json");
                    if (Files.exists(backendPath)) {
                        is = Files.newInputStream(backendPath);
                        logger.info("Loaded ledger.json from ../backend/data/ledger.json");
                    }
                }
            }

            if (is != null) {
                try (InputStream stream = is) {
                    rawLedger = objectMapper.readTree(stream);
                }
            } else {
                logger.warn("Could not find ledger.json in classpath or relative paths.");
                rawLedger = objectMapper.createObjectNode();
            }

            accountMap.clear();
            categoryMap.clear();
            transactionList.clear();
            rawAccountList.clear();

            if (rawLedger.has("accounts") && rawLedger.get("accounts").isArray()) {
                for (JsonNode acc : rawLedger.get("accounts")) {
                    rawAccountList.add(acc);
                    if (acc.has("id")) {
                        accountMap.put(acc.get("id").asText(), acc);
                    }
                }
            }

            if (rawLedger.has("categories") && rawLedger.get("categories").isArray()) {
                for (JsonNode cat : rawLedger.get("categories")) {
                    if (cat.has("name")) {
                        categoryMap.put(cat.get("name").asText(), cat);
                    }
                }
            }

            if (rawLedger.has("transactions") && rawLedger.get("transactions").isArray()) {
                for (JsonNode tx : rawLedger.get("transactions")) {
                    transactionList.add(tx);
                }
            }

            logger.info("Ledger initialized: {} accounts, {} transactions, {} categories",
                    rawAccountList.size(), transactionList.size(), categoryMap.size());

        } catch (Exception e) {
            logger.error("Failed to load ledger: {}", e.getMessage(), e);
        }
    }

    public List<JsonNode> getTransactions() {
        return transactionList;
    }

    public ToolResult getAccountBalances() {
        try {
            double totalBalance = 0.0;
            List<AccountItem> accounts = new ArrayList<>();

            for (JsonNode acc : rawAccountList) {
                totalBalance += acc.path("balance").asDouble(0.0);
            }

            for (JsonNode acc : rawAccountList) {
                double bal = round(acc.path("balance").asDouble(0.0), 2);
                double weight = totalBalance > 0 ? round(bal / totalBalance, 4) : 0.0;
                accounts.add(new AccountItem(
                        acc.path("id").asText(""),
                        acc.path("name").asText("Account"),
                        acc.path("type").asText("Bank"),
                        bal,
                        round(acc.path("initialBalance").asDouble(0.0), 2),
                        weight,
                        acc.path("color").asText("#6366f1"),
                        acc.path("isDefault").asBoolean(false)
                ));
            }

            accounts.sort((a, b) -> Double.compare(b.getBalance(), a.getBalance()));

            StringBuilder breakdown = new StringBuilder();
            for (AccountItem a : accounts) {
                if (breakdown.length() > 0) breakdown.append(", ");
                breakdown.append(a.getName())
                        .append(": Rs. ")
                        .append(CURRENCY_FMT.format(a.getBalance()))
                        .append(" (")
                        .append(String.format(Locale.US, "%.1f%%", a.getWeight() * 100))
                        .append(")");
            }

            String interpretation = String.format(
                    Locale.US,
                    "Total liquid balance across %d accounts is Rs. %s. Breakdown: %s.",
                    accounts.size(),
                    CURRENCY_FMT.format(totalBalance),
                    breakdown
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("total_balance", round(totalBalance, 2));
            valMap.put("account_count", accounts.size());
            valMap.put("accounts", accounts);

            return new ToolResult(valMap, "NPR", "deterministic_ledger_sum", Map.of(), interpretation);
        } catch (Exception e) {
            logger.error("Error in getAccountBalances: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "deterministic_ledger_sum", Map.of(), "Failed to retrieve account balances: " + e.getMessage());
        }
    }

    public ToolResult getSpendingSummary(String startDate, String endDate) {
        try {
            double totalIncome = 0.0;
            double totalExpense = 0.0;
            double totalTransfer = 0.0;
            int txCount = 0;

            for (JsonNode t : transactionList) {
                String d = t.path("date").asText("");
                if (startDate != null && !startDate.isBlank() && d.compareTo(startDate) < 0) continue;
                if (endDate != null && !endDate.isBlank() && d.compareTo(endDate) > 0) continue;

                txCount++;
                double amt = t.path("amount").asDouble(0.0);
                String type = t.path("type").asText("");
                if ("Income".equalsIgnoreCase(type)) {
                    totalIncome += amt;
                } else if ("Expense".equalsIgnoreCase(type)) {
                    totalExpense += amt;
                } else if ("Transfer".equalsIgnoreCase(type)) {
                    totalTransfer += amt;
                }
            }

            double netSavings = totalIncome - totalExpense;
            double savingsRate = totalIncome > 0 ? (netSavings / totalIncome * 100.0) : 0.0;

            String timeFrame = (startDate != null || endDate != null)
                    ? "between " + (startDate != null ? startDate : "start") + " and " + (endDate != null ? endDate : "present")
                    : "all-time";

            String interpretation = String.format(
                    Locale.US,
                    "Over %s across %,d transactions: Total Income is Rs. %s, Total Expenses are Rs. %s, " +
                    "resulting in a net %s of Rs. %s (Savings Rate: %.1f%%).",
                    timeFrame,
                    txCount,
                    CURRENCY_FMT.format(totalIncome),
                    CURRENCY_FMT.format(totalExpense),
                    netSavings >= 0 ? "surplus" : "deficit",
                    CURRENCY_FMT.format(Math.abs(netSavings)),
                    savingsRate
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("total_income", round(totalIncome, 2));
            valMap.put("total_expense", round(totalExpense, 2));
            valMap.put("total_transfer", round(totalTransfer, 2));
            valMap.put("net_savings", round(netSavings, 2));
            valMap.put("savings_rate_pct", round(savingsRate, 2));
            valMap.put("transaction_count", txCount);

            Map<String, Object> inputs = new HashMap<>();
            inputs.put("start_date", startDate);
            inputs.put("end_date", endDate);

            return new ToolResult(valMap, "NPR and percentage", "deterministic_cashflow_aggregation", inputs, interpretation);
        } catch (Exception e) {
            logger.error("Error in getSpendingSummary: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "deterministic_cashflow_aggregation", Map.of(), "Failed to compute spending summary: " + e.getMessage());
        }
    }

    public ToolResult getCategoryBreakdown(String transactionType, Integer topN, String startDate, String endDate) {
        String type = (transactionType != null && !transactionType.isBlank()) ? transactionType : "Expense";
        int limit = (topN != null && topN > 0) ? topN : 10;

        try {
            Map<String, Double> catAmounts = new HashMap<>();
            Map<String, Integer> catCounts = new HashMap<>();
            double totalTypeAmount = 0.0;

            for (JsonNode t : transactionList) {
                if (!type.equalsIgnoreCase(t.path("type").asText(""))) continue;

                String d = t.path("date").asText("");
                if (startDate != null && !startDate.isBlank() && d.compareTo(startDate) < 0) continue;
                if (endDate != null && !endDate.isBlank() && d.compareTo(endDate) > 0) continue;

                double amt = t.path("amount").asDouble(0.0);
                String cat = t.path("category").asText("Uncategorized");
                if (cat.isBlank()) cat = "Uncategorized";

                catAmounts.put(cat, catAmounts.getOrDefault(cat, 0.0) + amt);
                catCounts.put(cat, catCounts.getOrDefault(cat, 0) + 1);
                totalTypeAmount += amt;
            }

            final double finalTotal = totalTypeAmount;
            List<Map.Entry<String, Double>> sorted = catAmounts.entrySet().stream()
                    .sorted((a, b) -> Double.compare(b.getValue(), a.getValue()))
                    .limit(limit)
                    .toList();

            List<CategorySummary> categoryList = new ArrayList<>();
            for (Map.Entry<String, Double> entry : sorted) {
                String catName = entry.getKey();
                double amt = entry.getValue();
                double pct = finalTotal > 0 ? round(amt / finalTotal, 4) : 0.0;
                JsonNode meta = categoryMap.get(catName);
                String color = meta != null ? meta.path("color").asText(null) : null;
                String icon = meta != null ? meta.path("icon").asText(null) : null;

                categoryList.add(new CategorySummary(
                        catName,
                        round(amt, 2),
                        pct,
                        catCounts.getOrDefault(catName, 0),
                        color,
                        icon
                ));
            }

            StringBuilder topSummary = new StringBuilder();
            int previewCount = Math.min(5, categoryList.size());
            for (int i = 0; i < previewCount; i++) {
                CategorySummary c = categoryList.get(i);
                if (topSummary.length() > 0) topSummary.append(", ");
                topSummary.append(c.getCategory())
                        .append(": Rs. ")
                        .append(CURRENCY_FMT.format(c.getAmount()))
                        .append(" (")
                        .append(String.format(Locale.US, "%.1f%%", c.getPercentage() * 100))
                        .append(")");
            }

            String interpretation = String.format(
                    Locale.US,
                    "Top %d %s categories out of Rs. %s total: %s.",
                    categoryList.size(),
                    type.toLowerCase(Locale.US),
                    CURRENCY_FMT.format(totalTypeAmount),
                    topSummary
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("transaction_type", type);
            valMap.put("total_amount", round(totalTypeAmount, 2));
            valMap.put("top_categories", categoryList);
            valMap.put("all_categories_count", catAmounts.size());

            Map<String, Object> inputs = new HashMap<>();
            inputs.put("transaction_type", type);
            inputs.put("top_n", limit);

            return new ToolResult(valMap, "NPR and ratio", "category_aggregation", inputs, interpretation);
        } catch (Exception e) {
            logger.error("Error in getCategoryBreakdown: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "category_aggregation", Map.of(), "Failed to compute category breakdown: " + e.getMessage());
        }
    }

    public ToolResult queryLedgerTransactions(String query, String category, String accountName,
                                              String transactionType, Double minAmount, Double maxAmount, Integer limit) {
        int maxLimit = (limit != null && limit > 0) ? limit : 15;
        try {
            String qLower = (query != null && !query.isBlank()) ? query.toLowerCase(Locale.US) : null;
            String catLower = (category != null && !category.isBlank()) ? category.toLowerCase(Locale.US) : null;
            String accLower = (accountName != null && !accountName.isBlank()) ? accountName.toLowerCase(Locale.US) : null;
            String typeLower = (transactionType != null && !transactionType.isBlank()) ? transactionType.toLowerCase(Locale.US) : null;

            List<TransactionRecord> matches = new ArrayList<>();

            for (JsonNode t : transactionList) {
                String tType = t.path("type").asText("");
                String tCat = t.path("category").asText("");
                String tDesc = t.path("description").asText("");
                double amt = t.path("amount").asDouble(0.0);

                String accId = t.path("accountId").asText("");
                JsonNode accNode = accountMap.get(accId);
                String tAccName = accNode != null ? accNode.path("name").asText("Unknown Account") : "Unknown Account";

                if (typeLower != null && !tType.toLowerCase(Locale.US).equals(typeLower)) continue;
                if (catLower != null && !tCat.toLowerCase(Locale.US).contains(catLower)) continue;
                if (accLower != null && !tAccName.toLowerCase(Locale.US).contains(accLower)) continue;
                if (minAmount != null && amt < minAmount) continue;
                if (maxAmount != null && amt > maxAmount) continue;

                if (qLower != null) {
                    boolean found = tDesc.toLowerCase(Locale.US).contains(qLower)
                            || tCat.toLowerCase(Locale.US).contains(qLower)
                            || tAccName.toLowerCase(Locale.US).contains(qLower);
                    if (!found) continue;
                }

                String fullDate = t.path("date").asText("");
                String dateOnly = fullDate.length() >= 10 ? fullDate.substring(0, 10) : fullDate;

                matches.add(new TransactionRecord(
                        t.path("id").asText(""),
                        dateOnly,
                        tType,
                        round(amt, 2),
                        tDesc,
                        tCat,
                        tAccName
                ));
            }

            matches.sort((a, b) -> b.getDate().compareTo(a.getDate()));

            double totalMatchedAmt = matches.stream().mapToDouble(TransactionRecord::getAmount).sum();
            int totalMatched = matches.size();
            List<TransactionRecord> returnedMatches = matches.stream().limit(maxLimit).toList();

            String interpretation = String.format(
                    Locale.US,
                    "Found %d transactions matching criteria totaling Rs. %s. Returning the most recent %d.",
                    totalMatched,
                    CURRENCY_FMT.format(totalMatchedAmt),
                    returnedMatches.size()
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("total_matched", totalMatched);
            valMap.put("total_matched_amount", round(totalMatchedAmt, 2));
            valMap.put("transactions", returnedMatches);

            Map<String, Object> inputs = new HashMap<>();
            inputs.put("query", query);
            inputs.put("category", category);
            inputs.put("account", accountName);
            inputs.put("type", transactionType);

            return new ToolResult(valMap, "transactions", "deterministic_ledger_filter", inputs, interpretation);
        } catch (Exception e) {
            logger.error("Error in queryLedgerTransactions: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "deterministic_ledger_filter", Map.of(), "Failed to filter transactions: " + e.getMessage());
        }
    }

    public ToolResult getMonthlyCashflow() {
        try {
            Map<String, double[]> monthlyMap = new HashMap<>(); // [income, expense, transfer]

            for (JsonNode t : transactionList) {
                String d = t.path("date").asText("");
                if (d.length() < 7) continue;
                String monthKey = d.substring(0, 7); // YYYY-MM

                monthlyMap.putIfAbsent(monthKey, new double[3]);
                double[] values = monthlyMap.get(monthKey);
                double amt = t.path("amount").asDouble(0.0);
                String type = t.path("type").asText("");

                if ("Income".equalsIgnoreCase(type)) {
                    values[0] += amt;
                } else if ("Expense".equalsIgnoreCase(type)) {
                    values[1] += amt;
                } else if ("Transfer".equalsIgnoreCase(type)) {
                    values[2] += amt;
                }
            }

            List<String> sortedMonths = new ArrayList<>(monthlyMap.keySet());
            Collections.sort(sortedMonths);

            List<MonthlyCashflow> cashflowList = new ArrayList<>();
            for (String m : sortedMonths) {
                double[] vals = monthlyMap.get(m);
                double inc = round(vals[0], 2);
                double exp = round(vals[1], 2);
                double net = round(inc - exp, 2);
                cashflowList.add(new MonthlyCashflow(m, inc, exp, net));
            }

            StringBuilder recentTrajectory = new StringBuilder();
            int startIdx = Math.max(0, cashflowList.size() - 3);
            for (int i = startIdx; i < cashflowList.size(); i++) {
                MonthlyCashflow cf = cashflowList.get(i);
                if (recentTrajectory.length() > 0) recentTrajectory.append("; ");
                recentTrajectory.append(cf.getMonth())
                        .append(" (Inc: Rs. ")
                        .append(CURRENCY_FMT.format(cf.getIncome()))
                        .append(", Exp: Rs. ")
                        .append(CURRENCY_FMT.format(cf.getExpense()))
                        .append(", Net: Rs. ")
                        .append(CURRENCY_FMT.format(cf.getNet()))
                        .append(")");
            }

            String interpretation = String.format(
                    Locale.US,
                    "Analyzed %d active months. Recent trajectory: %s.",
                    cashflowList.size(),
                    recentTrajectory
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("months_count", cashflowList.size());
            valMap.put("monthly_cashflow", cashflowList);

            return new ToolResult(valMap, "NPR per month", "monthly_aggregation", Map.of(), interpretation);
        } catch (Exception e) {
            logger.error("Error in getMonthlyCashflow: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "monthly_aggregation", Map.of(), "Failed to compute monthly cashflow: " + e.getMessage());
        }
    }

    public ToolResult calculateFinancialHealthMetrics() {
        try {
            ToolResult balancesRes = getAccountBalances();
            Map<?, ?> bVal = (Map<?, ?>) balancesRes.getValue();
            double totalLiquid = bVal.containsKey("total_balance") ? ((Number) bVal.get("total_balance")).doubleValue() : 0.0;

            ToolResult cashflowRes = getMonthlyCashflow();
            Map<?, ?> cVal = (Map<?, ?>) cashflowRes.getValue();
            @SuppressWarnings("unchecked")
            List<MonthlyCashflow> monthly = (List<MonthlyCashflow>) cVal.get("monthly_cashflow");

            if (monthly == null || monthly.isEmpty()) {
                return new ToolResult(Map.of("runway_months", 0.0, "total_liquid", totalLiquid),
                        "metrics", "runway_diagnostics", Map.of(), "Insufficient monthly data to compute runway.");
            }

            double totalExp = monthly.stream().mapToDouble(MonthlyCashflow::getExpense).sum();
            double totalInc = monthly.stream().mapToDouble(MonthlyCashflow::getIncome).sum();
            double avgMonthlyExp = monthly.size() > 0 ? (totalExp / monthly.size()) : 1.0;

            double runwayMonths = avgMonthlyExp > 0 ? round(totalLiquid / avgMonthlyExp, 2) : 0.0;
            double overallSavingsRate = totalInc > 0 ? round(((totalInc - totalExp) / totalInc * 100.0), 2) : 0.0;

            String interpretation = String.format(
                    Locale.US,
                    "Current liquid funds of Rs. %s provide approximately %.1f months of emergency runway " +
                    "based on an average monthly burn rate of Rs. %s. Overall net savings rate is %.1f%%.",
                    CURRENCY_FMT.format(totalLiquid),
                    runwayMonths,
                    CURRENCY_FMT.format(avgMonthlyExp),
                    overallSavingsRate
            );

            Map<String, Object> valMap = new LinkedHashMap<>();
            valMap.put("total_liquid_reserves", round(totalLiquid, 2));
            valMap.put("average_monthly_expense", round(avgMonthlyExp, 2));
            valMap.put("emergency_runway_months", runwayMonths);
            valMap.put("overall_savings_rate_pct", overallSavingsRate);
            valMap.put("months_evaluated", monthly.size());

            return new ToolResult(valMap, "months and NPR", "runway_diagnostics", Map.of(), interpretation);
        } catch (Exception e) {
            logger.error("Error in calculateFinancialHealthMetrics: {}", e.getMessage(), e);
            return new ToolResult(Map.of(), "error", "runway_diagnostics", Map.of(), "Failed to calculate financial health metrics: " + e.getMessage());
        }
    }

    public PortfolioResponse buildPortfolioResponse() {
        ToolResult balancesRes = getAccountBalances();
        ToolResult spendingRes = getSpendingSummary(null, null);
        ToolResult categoryRes = getCategoryBreakdown("Expense", 10, null, null);
        ToolResult cashflowRes = getMonthlyCashflow();
        ToolResult txRes = queryLedgerTransactions(null, null, null, null, null, null, 10);

        @SuppressWarnings("unchecked")
        Map<String, Object> bVal = (Map<String, Object>) balancesRes.getValue();
        @SuppressWarnings("unchecked")
        Map<String, Object> sVal = (Map<String, Object>) spendingRes.getValue();
        @SuppressWarnings("unchecked")
        Map<String, Object> catVal = (Map<String, Object>) categoryRes.getValue();
        @SuppressWarnings("unchecked")
        Map<String, Object> cfVal = (Map<String, Object>) cashflowRes.getValue();
        @SuppressWarnings("unchecked")
        Map<String, Object> tVal = (Map<String, Object>) txRes.getValue();

        double totalBalance = bVal.containsKey("total_balance") ? ((Number) bVal.get("total_balance")).doubleValue() : 0.0;
        double totalIncome = sVal.containsKey("total_income") ? ((Number) sVal.get("total_income")).doubleValue() : 0.0;
        double totalExpense = sVal.containsKey("total_expense") ? ((Number) sVal.get("total_expense")).doubleValue() : 0.0;
        double netCashflow = sVal.containsKey("net_savings") ? ((Number) sVal.get("net_savings")).doubleValue() : 0.0;
        double savingsRate = sVal.containsKey("savings_rate_pct") ? ((Number) sVal.get("savings_rate_pct")).doubleValue() : 0.0;
        int txCount = sVal.containsKey("transaction_count") ? ((Number) sVal.get("transaction_count")).intValue() : 0;

        @SuppressWarnings("unchecked")
        List<AccountItem> accounts = (List<AccountItem>) bVal.getOrDefault("accounts", Collections.emptyList());
        @SuppressWarnings("unchecked")
        List<CategorySummary> topCategories = (List<CategorySummary>) catVal.getOrDefault("top_categories", Collections.emptyList());
        @SuppressWarnings("unchecked")
        List<MonthlyCashflow> monthlyList = (List<MonthlyCashflow>) cfVal.getOrDefault("monthly_cashflow", Collections.emptyList());
        @SuppressWarnings("unchecked")
        List<TransactionRecord> recentTxs = (List<TransactionRecord>) tVal.getOrDefault("transactions", Collections.emptyList());

        List<Holding> holdings = new ArrayList<>();
        Map<String, Double> weights = new HashMap<>();
        for (AccountItem acc : accounts) {
            holdings.add(new Holding(acc.getName(), 1.0, acc.getBalance(), acc.getBalance(), acc.getWeight(), acc.getType()));
            weights.put(acc.getName(), acc.getWeight());
        }

        Map<String, Double> sectors = new HashMap<>();
        for (CategorySummary cat : topCategories) {
            sectors.put(cat.getCategory(), cat.getPercentage());
        }

        PortfolioResponse response = new PortfolioResponse();
        response.setTotalBalance(totalBalance);
        response.setTotalIncome(totalIncome);
        response.setTotalExpense(totalExpense);
        response.setNetCashflow(netCashflow);
        response.setSavingsRate(savingsRate);
        response.setTransactionCount(txCount);
        response.setAccounts(accounts);
        response.setTopCategories(topCategories);
        response.setMonthlyCashflow(monthlyList);
        response.setRecentTransactions(recentTxs);

        response.setHoldings(holdings);
        response.setCash(totalBalance);
        response.setTotalValue(totalBalance);
        response.setWeights(weights);
        response.setSectors(sectors);

        return response;
    }

    private static double round(double val, int decimals) {
        double factor = Math.pow(10, decimals);
        return Math.round(val * factor) / factor;
    }
}
