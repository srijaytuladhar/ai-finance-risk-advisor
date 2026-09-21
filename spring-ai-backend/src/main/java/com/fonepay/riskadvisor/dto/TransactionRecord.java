package com.fonepay.riskadvisor.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class TransactionRecord {
    private String id;
    private String date;
    private String type;
    private double amount;
    private String description;
    private String category;
    @JsonProperty("account_name")
    private String accountName;

    public TransactionRecord() {}

    public TransactionRecord(String id, String date, String type, double amount, String description, String category, String accountName) {
        this.id = id;
        this.date = date;
        this.type = type;
        this.amount = amount;
        this.description = description;
        this.category = category;
        this.accountName = accountName;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getDate() { return date; }
    public void setDate(String date) { this.date = date; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public double getAmount() { return amount; }
    public void setAmount(double amount) { this.amount = amount; }

    public String getDescription() { return description; }
    public void setDescription(String description) { this.description = description; }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public String getAccountName() { return accountName; }
    public void setAccountName(String accountName) { this.accountName = accountName; }
}
