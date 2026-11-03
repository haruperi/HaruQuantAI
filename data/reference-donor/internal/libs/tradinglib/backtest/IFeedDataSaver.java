/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.tradinglib.backtest.HashPair;

public interface IFeedDataSaver {
    public void beforeSave(HashPair[] var1);

    public void setParams(boolean var1, int var2);

    public void saveTick(VersatileData var1) throws Exception;

    public void afterSave();
}

