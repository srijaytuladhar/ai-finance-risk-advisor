package com.fonepay.riskadvisor.service;

import com.fonepay.riskadvisor.dto.ChatRequest;
import com.fonepay.riskadvisor.dto.ChatResponse;
import com.fonepay.riskadvisor.dto.ToolCallRecord;
import com.fonepay.riskadvisor.tools.LedgerTools;
import com.fonepay.riskadvisor.tools.ToolExecutionTracker;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.AssistantMessage;
import org.springframework.ai.chat.messages.Message;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

@Service
public class AdvisorAgentService {
    private static final Logger logger = LoggerFactory.getLogger(AdvisorAgentService.class);

    public static final String SYSTEM_PROMPT = """
            You are a senior Fintech Financial & Risk Advisor specializing in personal finance, budget analytics, and cash flow risk diagnostics.
            Your core mission is to provide accurate, reliable, and deeply actionable financial guidance based on the user's authentic financial ledger (`ledger.json`).

            The user manages accounts across Nepalese financial institutions:
            - Citizen Bank (Primary Bank Account)
            - eSewa (Default Digital Wallet)
            - Cash (Physical Currency)
            - Prabhu Bank (Secondary Bank Account)
            - Laxmi Bank (Secondary Bank Account)
            All monetary figures are in Nepalese Rupees (Rs. / NPR).

            CRITICAL OPERATIONAL RULES:
            1. DETERMINISTIC ARITHMETIC ENFORCEMENT:
               - You have access to deterministic tools for all calculations.
               - NEVER mentally compute or guess numbers yourself. ALWAYS invoke the appropriate tool:
                 * For account balances, net liquid worth, or account distribution: call `get_account_balances`.
                 * For overall cash flow, total income, total expenses, and savings rate: call `get_spending_summary`.
                 * For category spending breakdown (e.g., Renovation, Tech, Eating Out, Chiya, Bike): call `get_category_breakdown`.
                 * For specific transaction lookups, filtering, or history: call `query_ledger_transactions`.
                 * For month-by-month trajectory and trends: call `get_monthly_cashflow`.
                 * For runway, emergency reserves, and burn rate: call `calculate_financial_health_metrics`.
               - Do NOT invent, approximate, or hallucinate numerical values.

            2. LEDGER RAG & CONTEXTUAL RETRIEVAL:
               - When the user asks descriptive questions about past events, trips (e.g., Manang vacation), vehicle maintenance (Bike servicing), specific persons/contacts (Dad, Roslina, Unish), or lifestyle habits, invoke `search_ledger_docs` or `query_ledger_transactions`.

            3. ACTIONABLE SYNTHESIS & PRESENTATION:
               - State financial metrics clearly using standard formatting: e.g., "Rs. 165,500.30" or "Rs. 268,910.00".
               - Highlight key takeaways using clean markdown (bold numbers, bulleted lists, and concise risk takeaways).
               - Leverage the tool's returned "interpretation" field for exact figures and context.
               - When asked for advice, balance positive financial habits with constructive risk alerts.
            """;

    private final ChatClient chatClient;
    private final ToolExecutionTracker tracker;

    @Value("${spring.ai.openai.chat.options.model:openai/gpt-4o-mini}")
    private String modelName;

    public AdvisorAgentService(ChatModel chatModel, LedgerTools ledgerTools, ToolExecutionTracker tracker) {
        this.tracker = tracker;
        this.chatClient = ChatClient.builder(chatModel)
                .defaultSystem(SYSTEM_PROMPT)
                .defaultTools(ledgerTools)
                .build();
    }

    public String getModelName() {
        return modelName;
    }

    public ChatResponse processQuery(ChatRequest request) {
        if (request == null || request.getMessage() == null || request.getMessage().isBlank()) {
            return new ChatResponse("Query message cannot be empty.", List.of(), List.of());
        }

        tracker.clear();
        logger.info("Processing user query: '{}'", request.getMessage());

        try {
            List<Message> historyMessages = new ArrayList<>();
            if (request.getHistory() != null) {
                for (Map<String, String> turn : request.getHistory()) {
                    String role = turn.get("role");
                    String content = turn.get("content");
                    if ("user".equalsIgnoreCase(role)) {
                        historyMessages.add(new UserMessage(content));
                    } else if ("assistant".equalsIgnoreCase(role)) {
                        historyMessages.add(new AssistantMessage(content));
                    }
                }
            }

            var promptSpec = chatClient.prompt();
            if (!historyMessages.isEmpty()) {
                promptSpec = promptSpec.messages(historyMessages);
            }

            String responseText = promptSpec.user(request.getMessage())
                    .call()
                    .content();

            List<ToolCallRecord> toolCalls = tracker.getToolCalls();
            List<String> sources = tracker.getSources();

            logger.info("Agent responded successfully. Executed {} tools, {} sources.", toolCalls.size(), sources.size());

            return new ChatResponse(responseText, toolCalls, sources);

        } catch (Exception e) {
            logger.error("Error during advisor chat execution: {}", e.getMessage(), e);
            throw new RuntimeException("Advisor reasoning failed: " + e.getMessage(), e);
        }
    }
}
