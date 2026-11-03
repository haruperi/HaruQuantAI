/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation;

public class CorrelationResult {
    public String symbol1;
    public String symbol2;
    public double value;

    public CorrelationResult(String symbol1, String symbol2) {
        this.symbol1 = symbol1;
        this.symbol2 = symbol2;
    }
}

