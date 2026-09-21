package com.fonepay.riskadvisor.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.fonepay.riskadvisor.dto.PortfolioResponse;
import com.fonepay.riskadvisor.dto.ToolResult;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

public class LedgerServiceTest {

    private LedgerService ledgerService;

    @BeforeEach
    void setUp() {
        ledgerService = new LedgerService(new ObjectMapper());
        ledgerService.init();
    }

    @Test
    void testGetAccountBalances() {
        ToolResult result = ledgerService.getAccountBalances();
        assertNotNull(result);
        assertEquals("NPR", result.getUnit());
        assertTrue(result.getValue() instanceof Map);

        @SuppressWarnings("unchecked")
        Map<String, Object> valMap = (Map<String, Object>) result.getValue();
        double totalBalance = ((Number) valMap.get("total_balance")).doubleValue();
        assertTrue(totalBalance > 0, "Total balance should be positive");

        int count = ((Number) valMap.get("account_count")).intValue();
        assertTrue(count >= 5, "Should have at least 5 accounts (Citizen, eSewa, etc.)");
    }

    @Test
    void testGetSpendingSummary() {
        ToolResult result = ledgerService.getSpendingSummary(null, null);
        assertNotNull(result);
        assertTrue(result.getValue() instanceof Map);

        @SuppressWarnings("unchecked")
        Map<String, Object> valMap = (Map<String, Object>) result.getValue();
        double totalIncome = ((Number) valMap.get("total_income")).doubleValue();
        double totalExpense = ((Number) valMap.get("total_expense")).doubleValue();
        int txCount = ((Number) valMap.get("transaction_count")).intValue();

        assertTrue(totalIncome > 0, "Total income should be positive");
        assertTrue(totalExpense > 0, "Total expense should be positive");
        assertTrue(txCount > 100, "Should have loaded authentic transactions from ledger.json");
    }

    @Test
    void testBuildPortfolioResponse() {
        PortfolioResponse response = ledgerService.buildPortfolioResponse();
        assertNotNull(response);
        assertTrue(response.getTotalBalance() > 0);
        assertFalse(response.getAccounts().isEmpty());
        assertFalse(response.getTopCategories().isEmpty());
        assertFalse(response.getMonthlyCashflow().isEmpty());
        assertFalse(response.getRecentTransactions().isEmpty());
    }
}
