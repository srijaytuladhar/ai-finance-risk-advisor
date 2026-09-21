package com.fonepay.riskadvisor.dto;

public class CategorySummary {
    private String category;
    private double amount;
    private double percentage;
    private int count;
    private String color;
    private String icon;

    public CategorySummary() {}

    public CategorySummary(String category, double amount, double percentage, int count, String color, String icon) {
        this.category = category;
        this.amount = amount;
        this.percentage = percentage;
        this.count = count;
        this.color = color;
        this.icon = icon;
    }

    public String getCategory() { return category; }
    public void setCategory(String category) { this.category = category; }

    public double getAmount() { return amount; }
    public void setAmount(double amount) { this.amount = amount; }

    public double getPercentage() { return percentage; }
    public void setPercentage(double percentage) { this.percentage = percentage; }

    public int getCount() { return count; }
    public void setCount(int count) { this.count = count; }

    public String getColor() { return color; }
    public void setColor(String color) { this.color = color; }

    public String getIcon() { return icon; }
    public void setIcon(String icon) { this.icon = icon; }
}
