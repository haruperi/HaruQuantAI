/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;

public abstract class ComputedDataSeries
extends DataSeries {
    public DataSeries Open;
    public DataSeries High;
    public DataSeries Low;
    public DataSeries Close;
    public DataSeries Volume;

    public ComputedDataSeries(DataSeries dataSeries, DataSeries dataSeries2, DataSeries dataSeries3, DataSeries dataSeries4, DataSeries dataSeries5) {
        super(0, 0);
        this.Open = dataSeries;
        this.High = dataSeries2;
        this.Low = dataSeries3;
        this.Close = dataSeries4;
        this.Volume = dataSeries5;
    }

    @Override
    public double get(int n) throws TradingException {
        return this.computeValue(n);
    }

    public abstract double computeValue(int var1) throws TradingException;

    @Override
    public int size() {
        return this.Open.size();
    }

    @Override
    public void destroy() {
    }
}

