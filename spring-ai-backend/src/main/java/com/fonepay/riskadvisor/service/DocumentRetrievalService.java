package com.fonepay.riskadvisor.service;

import com.fasterxml.jackson.databind.JsonNode;
import com.fonepay.riskadvisor.dto.ToolResult;
import jakarta.annotation.PostConstruct;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.stereotype.Service;

import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

@Service
public class DocumentRetrievalService {
    private static final Logger logger = LoggerFactory.getLogger(DocumentRetrievalService.class);

    private final LedgerService ledgerService;

    public static class DocChunk {
        private final String source;
        private final String category;
        private final String content;

        public DocChunk(String source, String category, String content) {
            this.source = source;
            this.category = category;
            this.content = content;
        }

        public String getSource() { return source; }
        public String getCategory() { return category; }
        public String getContent() { return content; }
    }

    private final List<DocChunk> chunks = new ArrayList<>();

    public DocumentRetrievalService(LedgerService ledgerService) {
        this.ledgerService = ledgerService;
    }

    @PostConstruct
    public synchronized void init() {
        loadDocs();
    }

    public synchronized void loadDocs() {
        chunks.clear();
        try {
            PathMatchingResourcePatternResolver resolver = new PathMatchingResourcePatternResolver();
            Resource[] resources = resolver.getResources("classpath*:data/docs/*.md");
            for (Resource r : resources) {
                if (r.isReadable()) {
                    try (InputStream is = r.getInputStream()) {
                        String text = new String(is.readAllBytes(), StandardCharsets.UTF_8);
                        splitAndIndex(r.getFilename(), text);
                    }
                }
            }

            // Also check local folder if empty
            if (chunks.isEmpty()) {
                Path localDocs = Path.of("src/main/resources/data/docs");
                if (Files.exists(localDocs)) {
                    try (var stream = Files.walk(localDocs)) {
                        stream.filter(p -> p.toString().endsWith(".md")).forEach(p -> {
                            try {
                                String text = Files.readString(p, StandardCharsets.UTF_8);
                                splitAndIndex(p.getFileName().toString(), text);
                            } catch (Exception ignored) {}
                        });
                    }
                }
            }

            logger.info("Document retrieval service loaded {} knowledge chunks", chunks.size());
        } catch (Exception e) {
            logger.warn("Could not load markdown docs for retrieval: {}", e.getMessage());
        }
    }

    private void splitAndIndex(String source, String text) {
        String[] paragraphs = text.split("\n\\s*\\n");
        for (String p : paragraphs) {
            String trimmed = p.trim();
            if (!trimmed.isEmpty()) {
                chunks.add(new DocChunk(source, "financial_policy", trimmed));
            }
        }
    }

    public ToolResult searchDocs(String query) {
        logger.info("Executing searchDocs for query: {}", query);
        try {
            if (query == null || query.isBlank()) {
                return new ToolResult(List.of(), "documents", "keyword_similarity_search",
                        Map.of("query", ""), "Query was empty; returned no documents.");
            }

            String[] terms = query.toLowerCase(Locale.US).split("\\s+");
            List<Map.Entry<DocChunk, Integer>> scoredChunks = new ArrayList<>();

            for (DocChunk chunk : chunks) {
                String cLower = chunk.getContent().toLowerCase(Locale.US);
                int score = 0;
                for (String term : terms) {
                    if (term.length() > 2 && cLower.contains(term)) {
                        score += 2;
                    }
                }
                if (score > 0) {
                    scoredChunks.add(Map.entry(chunk, score));
                }
            }

            // Also search transactions if query matches trips/people/maintenance
            for (JsonNode t : ledgerService.getTransactions()) {
                String desc = t.path("description").asText("").toLowerCase(Locale.US);
                String cat = t.path("category").asText("").toLowerCase(Locale.US);
                int score = 0;
                for (String term : terms) {
                    if (term.length() > 2) {
                        if (desc.contains(term)) score += 3;
                        if (cat.contains(term)) score += 2;
                    }
                }
                if (score > 0) {
                    String snippet = String.format("Transaction on %s: %s (Category: %s, Amount: Rs. %.2f, Type: %s)",
                            t.path("date").asText(""),
                            t.path("description").asText(""),
                            t.path("category").asText(""),
                            t.path("amount").asDouble(0.0),
                            t.path("type").asText(""));
                    scoredChunks.add(Map.entry(new DocChunk("ledger.json", "transaction", snippet), score));
                }
            }

            scoredChunks.sort((a, b) -> Integer.compare(b.getValue(), a.getValue()));
            List<DocChunk> topDocs = scoredChunks.stream().limit(4).map(Map.Entry::getKey).toList();

            List<Map<String, String>> extracted = new ArrayList<>();
            List<String> summarySnippets = new ArrayList<>();

            for (DocChunk d : topDocs) {
                Map<String, String> item = new HashMap<>();
                item.put("source", d.getSource());
                item.put("category", d.getCategory());
                item.put("content", d.getContent());
                extracted.add(item);

                String preview = d.getContent().length() > 150 ? d.getContent().substring(0, 150) + "..." : d.getContent();
                summarySnippets.add("[" + d.getSource() + "]: " + preview);
            }

            String interpretation = extracted.isEmpty()
                    ? String.format("No relevant documentation found for query '%s'.", query)
                    : String.format("Found %d relevant excerpts addressing '%s': %s",
                    extracted.size(), query, String.join(" | ", summarySnippets));

            return new ToolResult(extracted, "document_chunks", "keyword_similarity_search",
                    Map.of("query", query), interpretation);

        } catch (Exception e) {
            logger.error("Error in searchDocs: {}", e.getMessage(), e);
            return new ToolResult(List.of(), "error", "keyword_similarity_search",
                    Map.of("query", query), "Error searching docs: " + e.getMessage());
        }
    }
}
