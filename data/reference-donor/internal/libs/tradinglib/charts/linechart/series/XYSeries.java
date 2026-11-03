/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.charts.linechart.series;

import com.strategyquant.tradinglib.charts.linechart.series.AbstractSeries;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;

public class XYSeries
extends AbstractSeries {
    public XYSeries(String string) {
        super(string);
    }

    public XYSeries(String string, int n) {
        super(string);
        this.capacity = n;
    }

    public synchronized void addValue(long l, double d) {
        XYValue xYValue = new XYValue(l, d, l + "");
        this.values.add(xYValue);
    }

    public synchronized void addValue(long l, double d, String string) {
        XYValue xYValue = new XYValue(l, d, string);
        this.values.add(xYValue);
    }
}

