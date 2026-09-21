package com.fonepay.riskadvisor.dto;

import java.util.HashMap;
import java.util.Map;

public class ToolCallRecord {
    private String name;
    private Map<String, Object> args = new HashMap<>();
    private Object result;

    public ToolCallRecord() {}

    public ToolCallRecord(String name, Map<String, Object> args, Object result) {
        this.name = name;
        this.args = args != null ? args : new HashMap<>();
        this.result = result;
    }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public Map<String, Object> getArgs() { return args; }
    public void setArgs(Map<String, Object> args) { this.args = args; }

    public Object getResult() { return result; }
    public void setResult(Object result) { this.result = result; }
}
