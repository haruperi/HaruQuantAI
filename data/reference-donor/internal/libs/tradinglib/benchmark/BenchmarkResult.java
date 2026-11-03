/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.benchmark;

public class BenchmarkResult {
    public static double TOTAL_TICKS = 1.3241836E7;
    public Throwable error;
    public String testName;
    public long testTime;
    public long dataLoadTime;
    public double strategyAverageTime;
    public double avgStrategiesPerHour;
    public int totalTrades;
    public double timePerTick;

    public BenchmarkResult(String string) {
        this.testName = string;
    }

    public void setError(Throwable throwable) {
        this.error = throwable;
    }

    public boolean isError() {
        return this.error != null;
    }

    public void setResult(long l, long l2, double d, double d2, int n) {
        this.testTime = l;
        this.dataLoadTime = l2;
        this.strategyAverageTime = d;
        this.avgStrategiesPerHour = d2;
        this.totalTrades = n;
        this.timePerTick = d / TOTAL_TICKS;
    }

    public String toString() {
        if (this.isError()) {
            return String.format("%s\t|\tTEST ERROR: %s", this.testName, this.error.getMessage());
        }
        return String.format("%s\t|\t%d ms.\t|\t%.2f\t|\t%.2f\t|\t%d\t|\t%.10f", this.testName, this.testTime, this.strategyAverageTime, this.avgStrategiesPerHour, this.totalTrades, this.timePerTick);
    }
}

