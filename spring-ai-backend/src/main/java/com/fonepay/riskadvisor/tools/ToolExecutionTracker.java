package com.fonepay.riskadvisor.tools;

import com.fonepay.riskadvisor.dto.ToolCallRecord;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Component
public class ToolExecutionTracker {
    private final ThreadLocal<List<ToolCallRecord>> toolCallsHolder = ThreadLocal.withInitial(ArrayList::new);
    private final ThreadLocal<List<String>> sourcesHolder = ThreadLocal.withInitial(ArrayList::new);

    public void clear() {
        toolCallsHolder.get().clear();
        sourcesHolder.get().clear();
    }

    public void record(String name, Map<String, Object> args, Object result) {
        toolCallsHolder.get().add(new ToolCallRecord(name, args, result));
    }

    public void addSource(String source) {
        if (source != null && !source.isBlank() && !sourcesHolder.get().contains(source)) {
            sourcesHolder.get().add(source);
        }
    }

    public List<ToolCallRecord> getToolCalls() {
        return new ArrayList<>(toolCallsHolder.get());
    }

    public List<String> getSources() {
        return new ArrayList<>(sourcesHolder.get());
    }
}
