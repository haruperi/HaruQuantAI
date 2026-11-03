/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project;

public class ChartSetupException
extends Exception {
    private int chartIndex;

    public ChartSetupException(int n, Exception exception) {
        super(exception);
        this.chartIndex = n;
    }

    public int getChartIndex() {
        return this.chartIndex;
    }
}

