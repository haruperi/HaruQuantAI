/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.TradingException;

public interface IDataSeriesChangeListener {
    public void changed(int var1, int var2) throws TradingException;
}

