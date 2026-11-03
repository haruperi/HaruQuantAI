/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.charts.linechart.series;

public class XYValue {
    public long x;
    public double y;
    public String xLabel;

    public XYValue(long l, double d) {
        this.x = l;
        this.y = d;
    }

    public XYValue(long l, double d, String string) {
        this.x = l;
        this.y = d;
        this.xLabel = string;
    }
}

