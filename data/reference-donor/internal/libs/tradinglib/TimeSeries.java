/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.charts.linechart.series.AbstractSeries;
import com.strategyquant.tradinglib.charts.linechart.series.XYValue;

public class TimeSeries
extends AbstractSeries {
    public TimeSeries(String string) {
        super(string);
    }

    public TimeSeries(String string, int n) {
        super(string);
        this.capacity = n;
    }

    public void addValue(long l, double d) {
        XYValue xYValue = new XYValue(l, d);
        this.values.add(xYValue);
    }
}

