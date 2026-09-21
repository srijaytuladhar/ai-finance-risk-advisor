package com.fonepay.riskadvisor.dto;

public class Holding {
    private String ticker;
    private double shares;
    private double price;
    private double value;
    private double weight;
    private String sector;

    public Holding() {}

    public Holding(String ticker, double shares, double price, double value, double weight, String sector) {
        this.ticker = ticker;
        this.shares = shares;
        this.price = price;
        this.value = value;
        this.weight = weight;
        this.sector = sector;
    }

    public String getTicker() { return ticker; }
    public void setTicker(String ticker) { this.ticker = ticker; }

    public double getShares() { return shares; }
    public void setShares(double shares) { this.shares = shares; }

    public double getPrice() { return price; }
    public void setPrice(double price) { this.price = price; }

    public double getValue() { return value; }
    public void setValue(double value) { this.value = value; }

    public double getWeight() { return weight; }
    public void setWeight(double weight) { this.weight = weight; }

    public String getSector() { return sector; }
    public void setSector(String sector) { this.sector = sector; }
}
