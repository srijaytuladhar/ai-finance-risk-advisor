package com.fonepay.riskadvisor.dto;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

public class ChatRequest {
    private String message;
    private List<Map<String, String>> history = new ArrayList<>();

    public ChatRequest() {}

    public ChatRequest(String message, List<Map<String, String>> history) {
        this.message = message;
        this.history = history != null ? history : new ArrayList<>();
    }

    public String getMessage() { return message; }
    public void setMessage(String message) { this.message = message; }

    public List<Map<String, String>> getHistory() { return history; }
    public void setHistory(List<Map<String, String>> history) { this.history = history; }
}
