/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.exchange;

public class SymbolInfo {
    private double pointValue = 1.0;
    private double tickSize = 1.0E-8;
    private double tickStep = 1.0E-8;
    private double defaultSpread = 0.0;
    private double defaultSlippage = 0.0;
    private long dateFrom;

    public double getPointValue() {
        return this.pointValue;
    }

    public void setPointValue(double d) {
        this.pointValue = d;
    }

    public double getTickSize() {
        return this.tickSize;
    }

    public void setTickSize(double d) {
        this.tickSize = d;
    }

    public double getTickStep() {
        return this.tickStep;
    }

    public void setTickStep(double d) {
        this.tickStep = d;
    }

    public double getDefaultSpread() {
        return this.defaultSpread;
    }

    public void setDefaultSpread(double d) {
        this.defaultSpread = d;
    }

    public double getDefaultSlippage() {
        return this.defaultSlippage;
    }

    public void setDefaultSlippage(double d) {
        this.defaultSlippage = d;
    }

    public long getDateFrom() {
        return this.dateFrom;
    }

    public void setDateFrom(long l) {
        this.dateFrom = l;
    }
}

