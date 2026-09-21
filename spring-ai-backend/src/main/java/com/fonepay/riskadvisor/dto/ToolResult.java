package com.fonepay.riskadvisor.dto;

import java.util.HashMap;
import java.util.Map;

public class ToolResult {
    private Object value;
    private String unit;
    private String method;
    private Map<String, Object> inputs = new HashMap<>();
    private String interpretation;

    public ToolResult() {}

    public ToolResult(Object value, String unit, String method, Map<String, Object> inputs, String interpretation) {
        this.value = value;
        this.unit = unit;
        this.method = method;
        this.inputs = inputs != null ? inputs : new HashMap<>();
        this.interpretation = interpretation;
    }

    public Object getValue() { return value; }
    public void setValue(Object value) { this.value = value; }

    public String getUnit() { return unit; }
    public void setUnit(String unit) { this.unit = unit; }

    public String getMethod() { return method; }
    public void setMethod(String method) { this.method = method; }

    public Map<String, Object> getInputs() { return inputs; }
    public void setInputs(Map<String, Object> inputs) { this.inputs = inputs; }

    public String getInterpretation() { return interpretation; }
    public void setInterpretation(String interpretation) { this.interpretation = interpretation; }
}
