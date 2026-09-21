package com.fonepay.riskadvisor.dto;

public class MonthlyCashflow {
    private String month;
    private double income;
    private double expense;
    private double net;

    public MonthlyCashflow() {}

    public MonthlyCashflow(String month, double income, double expense, double net) {
        this.month = month;
        this.income = income;
        this.expense = expense;
        this.net = net;
    }

    public String getMonth() { return month; }
    public void setMonth(String month) { this.month = month; }

    public double getIncome() { return income; }
    public void setIncome(double income) { this.income = income; }

    public double getExpense() { return expense; }
    public void setExpense(double expense) { this.expense = expense; }

    public double getNet() { return net; }
    public void setNet(double net) { this.net = net; }
}
