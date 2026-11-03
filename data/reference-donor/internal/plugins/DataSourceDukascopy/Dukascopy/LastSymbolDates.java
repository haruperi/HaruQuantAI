/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.DataSource.impl.Dukascopy;

import java.io.Serializable;

public class LastSymbolDates
implements Serializable {
    String symbol;
    long dateFrom;
    long dateTo;

    public LastSymbolDates(String symbol, long dateFrom, long dateTo) {
        this.symbol = symbol;
        this.dateFrom = dateFrom;
        this.dateTo = dateTo;
    }
}

