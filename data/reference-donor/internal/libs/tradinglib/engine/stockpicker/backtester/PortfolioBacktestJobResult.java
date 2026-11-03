/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.engine.stockpicker.backtester;

import java.io.Serializable;

public class PortfolioBacktestJobResult
implements Serializable {
    public String symbol;
    public int totalTicks;

    public PortfolioBacktestJobResult(String string, int n) {
        this.symbol = string;
        this.totalTicks = n;
    }
}

