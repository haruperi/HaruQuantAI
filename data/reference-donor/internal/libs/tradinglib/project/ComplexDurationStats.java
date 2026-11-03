/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

public class ComplexDurationStats {
    public String name = "Unknown";
    public int count = 0;
    public double avgTime = 0.0;
    public double totalTime = 0.0;

    public void update(String string, double d) {
        this.name = string;
        this.totalTime += d;
        this.avgTime = (this.avgTime * (double)this.count + d) / (double)(this.count + 1);
        ++this.count;
    }
}

