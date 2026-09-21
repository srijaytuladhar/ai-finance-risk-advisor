package com.fonepay.riskadvisor.controller;

import com.fonepay.riskadvisor.dto.PortfolioResponse;
import com.fonepay.riskadvisor.service.LedgerService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api")
public class PortfolioController {
    private static final Logger logger = LoggerFactory.getLogger(PortfolioController.class);

    private final LedgerService ledgerService;

    public PortfolioController(LedgerService ledgerService) {
        this.ledgerService = ledgerService;
    }

    @GetMapping("/portfolio")
    public ResponseEntity<PortfolioResponse> getPortfolio() {
        try {
            PortfolioResponse response = ledgerService.buildPortfolioResponse();
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Failed to build portfolio response: {}", e.getMessage(), e);
            throw new RuntimeException("Failed to retrieve portfolio data: " + e.getMessage(), e);
        }
    }

    @GetMapping("/ledger")
    public ResponseEntity<PortfolioResponse> getLedger() {
        return getPortfolio();
    }
}
