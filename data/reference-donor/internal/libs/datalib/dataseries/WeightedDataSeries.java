/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.ComputedDataSeries;

public class WeightedDataSeries
extends ComputedDataSeries {
    public WeightedDataSeries(DataSeries dataSeries, DataSeries dataSeries2, DataSeries dataSeries3, DataSeries dataSeries4, DataSeries dataSeries5) {
        super(dataSeries, dataSeries2, dataSeries3, dataSeries4, dataSeries5);
    }

    @Override
    public double computeValue(int n) throws TradingException {
        return (this.High.get(n) + this.Low.get(n) + this.Close.get(n) + this.Close.get(n)) / 4.0;
    }
}

