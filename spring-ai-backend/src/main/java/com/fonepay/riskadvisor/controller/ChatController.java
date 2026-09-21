package com.fonepay.riskadvisor.controller;

import com.fonepay.riskadvisor.dto.ChatRequest;
import com.fonepay.riskadvisor.dto.ChatResponse;
import com.fonepay.riskadvisor.service.AdvisorAgentService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.server.ResponseStatusException;

@RestController
@RequestMapping("/api")
public class ChatController {
    private static final Logger logger = LoggerFactory.getLogger(ChatController.class);

    private final AdvisorAgentService agentService;

    public ChatController(AdvisorAgentService agentService) {
        this.agentService = agentService;
    }

    @PostMapping("/chat")
    public ResponseEntity<ChatResponse> chat(@RequestBody ChatRequest request) {
        if (request == null || request.getMessage() == null || request.getMessage().trim().isEmpty()) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "User message cannot be empty.");
        }

        try {
            ChatResponse response = agentService.processQuery(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            logger.error("Chat agent execution encountered an error: {}", e.getMessage(), e);
            throw new ResponseStatusException(HttpStatus.INTERNAL_SERVER_ERROR, "Agent reasoning failed: " + e.getMessage(), e);
        }
    }
}
