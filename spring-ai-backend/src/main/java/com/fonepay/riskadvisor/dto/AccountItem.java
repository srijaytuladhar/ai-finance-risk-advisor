package com.fonepay.riskadvisor.dto;

import com.fasterxml.jackson.annotation.JsonProperty;

public class AccountItem {
    private String id;
    private String name;
    private String type;
    private double balance;
    @JsonProperty("initial_balance")
    private double initialBalance;
    private double weight;
    private String color;
    @JsonProperty("is_default")
    private boolean isDefault;

    public AccountItem() {}

    public AccountItem(String id, String name, String type, double balance, double initialBalance, double weight, String color, boolean isDefault) {
        this.id = id;
        this.name = name;
        this.type = type;
        this.balance = balance;
        this.initialBalance = initialBalance;
        this.weight = weight;
        this.color = color;
        this.isDefault = isDefault;
    }

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }

    public String getName() { return name; }
    public void setName(String name) { this.name = name; }

    public String getType() { return type; }
    public void setType(String type) { this.type = type; }

    public double getBalance() { return balance; }
    public void setBalance(double balance) { this.balance = balance; }

    public double getInitialBalance() { return initialBalance; }
    public void setInitialBalance(double initialBalance) { this.initialBalance = initialBalance; }

    public double getWeight() { return weight; }
    public void setWeight(double weight) { this.weight = weight; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public boolean isDefault() { return isDefault; }
    public void setDefault(boolean isDefault) { this.isDefault = isDefault; }
}
