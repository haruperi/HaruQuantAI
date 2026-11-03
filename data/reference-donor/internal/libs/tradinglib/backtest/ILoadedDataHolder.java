/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.strategy.MarketData;

public interface ILoadedDataHolder {
    public VersatileData getNextTick(VersatileData var1) throws Exception;

    public long size();

    public ILoadedDataHolder cloneHolder() throws Exception;

    public void beforeSave(HashPair[] var1) throws Exception;

    public void afterSave() throws Exception;

    public void saveTick(VersatileData var1) throws Exception;

    public void afterProduce();

    public void setParams(boolean var1, int var2);

    public HashPair[] getHashPairs();

    public void destroy();

    public void setMarketData(MarketData[] var1);

    public MarketData[] getMarketData();

    public long freeIfInMemory();
}

