/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades;

public class OverlappingTrade {
    public long from1;
    public long to1;
    public long from2;
    public long to2;
    public String time;

    public OverlappingTrade(long from1, long to1, long from2, long to2, String time) {
        this.from1 = from1;
        this.to1 = to1;
        this.from2 = from2;
        this.to2 = to2;
        this.time = time;
    }
}

