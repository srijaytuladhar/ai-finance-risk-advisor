package com.fonepay.riskadvisor.controller;

import com.fonepay.riskadvisor.service.AdvisorAgentService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

@RestController
@RequestMapping("/api")
public class HealthController {

    private final AdvisorAgentService agentService;

    public HealthController(AdvisorAgentService agentService) {
        this.agentService = agentService;
    }

    @GetMapping("/health")
    public ResponseEntity<Map<String, String>> healthCheck() {
        return ResponseEntity.ok(Map.of(
                "status", "ok",
                "service", "Fintech Financial & Ledger Risk Advisor (Spring AI)",
                "model", agentService.getModelName()
        ));
    }
}
