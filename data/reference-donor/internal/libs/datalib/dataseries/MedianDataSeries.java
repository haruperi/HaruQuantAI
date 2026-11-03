/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.ComputedDataSeries;

public class MedianDataSeries
extends ComputedDataSeries {
    public MedianDataSeries(DataSeries dataSeries, DataSeries dataSeries2, DataSeries dataSeries3, DataSeries dataSeries4, DataSeries dataSeries5) {
        super(dataSeries, dataSeries2, dataSeries3, dataSeries4, dataSeries5);
    }

    @Override
    public double computeValue(int n) throws TradingException {
        if (this.High == null || this.Low == null) {
            return -1.0;
        }
        return (this.High.get(n) + this.Low.get(n)) / 2.0;
    }
}

