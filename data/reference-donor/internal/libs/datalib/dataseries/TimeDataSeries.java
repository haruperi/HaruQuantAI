/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.TimeDataSeriesBase;

public class TimeDataSeries
extends TimeDataSeriesBase {
    public TimeDataSeries() {
    }

    public TimeDataSeries(int n) {
        super(n);
    }

    public TimeDataSeries(String string, int n) {
        super(n, string);
    }

    public TimeDataSeries(String string, int n, ChartDef chartDef) {
        super(n, string, chartDef);
    }

    public TimeDataSeries(int n, int n2) {
        super(n, n2);
    }

    public TimeDataSeries(String string) {
        super(100);
        this.setName(string);
    }

    public long get(int n) throws TradingException {
        return this._getLong(n);
    }

    public void set(int n, long l) throws TradingException {
        this._setLong(n, l);
    }

    public void addValues(int n) throws TradingException {
        this.addLongValues(n, 0L);
    }

    public void add(long l) throws TradingException {
        this._addLong(l);
    }
}

