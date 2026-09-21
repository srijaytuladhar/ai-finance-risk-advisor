package com.fonepay.riskadvisor.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

public class PortfolioResponse {
    @JsonProperty("total_balance")
    private double totalBalance;

    @JsonProperty("total_income")
    private double totalIncome;

    @JsonProperty("total_expense")
    private double totalExpense;

    @JsonProperty("net_cashflow")
    private double netCashflow;

    @JsonProperty("savings_rate")
    private double savingsRate;

    @JsonProperty("transaction_count")
    private int transactionCount;

    private List<AccountItem> accounts = new ArrayList<>();

    @JsonProperty("top_categories")
    private List<CategorySummary> topCategories = new ArrayList<>();

    @JsonProperty("monthly_cashflow")
    private List<MonthlyCashflow> monthlyCashflow = new ArrayList<>();

    @JsonProperty("recent_transactions")
    private List<TransactionRecord> recentTransactions = new ArrayList<>();

    // Backward compatibility fields
    private List<Holding> holdings = new ArrayList<>();
    private double cash;
    @JsonProperty("total_value")
    private double totalValue;
    private Map<String, Double> weights = new HashMap<>();
    private Map<String, Double> sectors = new HashMap<>();

    public PortfolioResponse() {}

    public double getTotalBalance() { return totalBalance; }
    public void setTotalBalance(double totalBalance) { this.totalBalance = totalBalance; }

    public double getTotalIncome() { return totalIncome; }
    public void setTotalIncome(double totalIncome) { this.totalIncome = totalIncome; }

    public double getTotalExpense() { return totalExpense; }
    public void setTotalExpense(double totalExpense) { this.totalExpense = totalExpense; }

    public double getNetCashflow() { return netCashflow; }
    public void setNetCashflow(double netCashflow) { this.netCashflow = netCashflow; }

    public double getSavingsRate() { return savingsRate; }
    public void setSavingsRate(double savingsRate) { this.savingsRate = savingsRate; }

    public int getTransactionCount() { return transactionCount; }
    public void setTransactionCount(int transactionCount) { this.transactionCount = transactionCount; }

    public List<AccountItem> getAccounts() { return accounts; }
    public void setAccounts(List<AccountItem> accounts) { this.accounts = accounts; }

    public List<CategorySummary> getTopCategories() { return topCategories; }
    public void setTopCategories(List<CategorySummary> topCategories) { this.topCategories = topCategories; }

    public List<MonthlyCashflow> getMonthlyCashflow() { return monthlyCashflow; }
    public void setMonthlyCashflow(List<MonthlyCashflow> monthlyCashflow) { this.monthlyCashflow = monthlyCashflow; }

    public List<TransactionRecord> getRecentTransactions() { return recentTransactions; }
    public void setRecentTransactions(List<TransactionRecord> recentTransactions) { this.recentTransactions = recentTransactions; }

    public List<Holding> getHoldings() { return holdings; }
    public void setHoldings(List<Holding> holdings) { this.holdings = holdings; }

    public double getCash() { return cash; }
    public void setCash(double cash) { this.cash = cash; }

    public double getTotalValue() { return totalValue; }
    public void setTotalValue(double totalValue) { this.totalValue = totalValue; }

    public Map<String, Double> getWeights() { return weights; }
    public void setWeights(Map<String, Double> weights) { this.weights = weights; }

    public Map<String, Double> getSectors() { return sectors; }
    public void setSectors(Map<String, Double> sectors) { this.sectors = sectors; }
}
