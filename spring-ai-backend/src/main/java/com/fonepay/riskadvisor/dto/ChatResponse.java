package com.fonepay.riskadvisor.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import java.util.ArrayList;
import java.util.List;

public class ChatResponse {
    private String response;

    @JsonProperty("tool_calls")
    private List<ToolCallRecord> toolCalls = new ArrayList<>();

    private List<String> sources = new ArrayList<>();

    public ChatResponse() {}

    public ChatResponse(String response, List<ToolCallRecord> toolCalls, List<String> sources) {
        this.response = response;
        this.toolCalls = toolCalls != null ? toolCalls : new ArrayList<>();
        this.sources = sources != null ? sources : new ArrayList<>();
    }

    public String getResponse() { return response; }
    public void setResponse(String response) { this.response = response; }

    public List<ToolCallRecord> getToolCalls() { return toolCalls; }
    public void setToolCalls(List<ToolCallRecord> toolCalls) { this.toolCalls = toolCalls; }

    public List<String> getSources() { return sources; }
    public void setSources(List<String> sources) { this.sources = sources; }
}
