/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.backtest.BacktestDataFeedElement;
import com.strategyquant.tradinglib.backtest.DataLoadStats;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.backtest.IFeedDataSaver;
import com.strategyquant.tradinglib.backtest.ILoadedDataHolder;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.strategy.MarketData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedDataHolderArray
implements ILoadedDataHolder,
IFeedDataSaver {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedDataHolderArray");
    private static int NUMBER_OF_ARRAYS = 2000;
    private static int MEMORY_INITIALIZATION_CHUNKS = 1000000;
    private BacktestDataFeedElement[][] data = null;
    private int arraysCount = 0;
    private int dataCount = 0;
    private HashPair[] hashPairs;
    private volatile boolean isLoaded = false;
    private int index = 0;
    private int hash;

    public LoadedDataHolderArray(int n, ILoadedDataHolder iLoadedDataHolder, DataLoadStats dataLoadStats, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        this.hash = n;
        this.hashPairs = iLoadedDataHolder.getHashPairs();
        this.loadDataToArray(iLoadedDataHolder, dataLoadStats);
    }

    public LoadedDataHolderArray(int n) {
        this.hash = n;
    }

    private void loadDataToArray(ILoadedDataHolder iLoadedDataHolder, DataLoadStats dataLoadStats) throws Exception {
        long l = System.currentTimeMillis();
        this.beforeSave(this.hashPairs);
        VersatileData versatileData = new VersatileData();
        while ((versatileData = iLoadedDataHolder.getNextTick(versatileData)) != null) {
            this.saveTick(versatileData);
        }
        dataLoadStats.loadingTime = System.currentTimeMillis() - l;
        Log.info("Data loaded ARRAY memory in " + dataLoadStats.loadingTime + " ms.");
    }

    @Override
    public void beforeSave(HashPair[] hashPairArray) {
        this.isLoaded = false;
        this.data = new BacktestDataFeedElement[NUMBER_OF_ARRAYS][];
        this.data[this.arraysCount++] = new BacktestDataFeedElement[MEMORY_INITIALIZATION_CHUNKS];
        this.index = 0;
    }

    @Override
    public void afterSave() {
    }

    @Override
    public ILoadedDataHolder cloneHolder() {
        LoadedDataHolderArray loadedDataHolderArray = new LoadedDataHolderArray(this.hash);
        loadedDataHolderArray.data = this.data;
        loadedDataHolderArray.arraysCount = this.arraysCount;
        loadedDataHolderArray.dataCount = this.dataCount;
        loadedDataHolderArray.isLoaded = this.isLoaded;
        loadedDataHolderArray.index = 0;
        loadedDataHolderArray.hashPairs = this.hashPairs;
        return loadedDataHolderArray;
    }

    @Override
    public void saveTick(VersatileData versatileData) throws Exception {
        if (versatileData.type == 1) {
            this.saveTickData(versatileData.time, versatileData.connectionHash, versatileData.symbolHash, versatileData.bid, versatileData.ask, versatileData.volume, versatileData.sessionStartTime);
        } else {
            this.saveMinuteData(versatileData.time, versatileData.connectionHash, versatileData.symbolHash, versatileData.open, versatileData.high, versatileData.low, versatileData.close, versatileData.volume, versatileData.sessionStartTime);
        }
    }

    private void saveTickData(long l, int n, int n2, double d, double d2, double d3, long l2) throws Exception {
        int n3 = this.dataCount / MEMORY_INITIALIZATION_CHUNKS;
        int n4 = this.dataCount - n3 * MEMORY_INITIALIZATION_CHUNKS;
        if (this.arraysCount <= n3) {
            this.data[this.arraysCount++] = new BacktestDataFeedElement[MEMORY_INITIALIZATION_CHUNKS];
        }
        this.data[n3][n4] = new BacktestDataFeedElement();
        this.data[n3][n4].setTickData(l, this.getHashPairIndex(n, n2), d, d2, d3, l2);
        ++this.dataCount;
    }

    private void saveMinuteData(long l, int n, int n2, double d, double d2, double d3, double d4, double d5, long l2) throws Exception {
        int n3 = this.dataCount / MEMORY_INITIALIZATION_CHUNKS;
        int n4 = this.dataCount - n3 * MEMORY_INITIALIZATION_CHUNKS;
        if (this.arraysCount <= n3) {
            this.data[this.arraysCount++] = new BacktestDataFeedElement[MEMORY_INITIALIZATION_CHUNKS];
        }
        this.data[n3][n4] = new BacktestDataFeedElement();
        this.data[n3][n4].setOhlcData(l, this.getHashPairIndex(n, n2), d, d2, d3, d4, d5, l2);
        ++this.dataCount;
    }

    private byte getHashPairIndex(int n, int n2) throws Exception {
        for (byte by = 0; by < this.hashPairs.length; by = (byte)((byte)(by + 1))) {
            if (this.hashPairs[by].connectionHash != n || this.hashPairs[by].symbolHash != n2) continue;
            return by;
        }
        throw new Exception(L.t((String)"HashPair for %d / %d was not found!", (Object[])new Object[]{n, n2}));
    }

    @Override
    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        if (this.index >= this.dataCount) {
            return null;
        }
        int n = this.index / MEMORY_INITIALIZATION_CHUNKS;
        int n2 = this.index - n * MEMORY_INITIALIZATION_CHUNKS;
        BacktestDataFeedElement backtestDataFeedElement = this.data[n][n2];
        versatileData.time = backtestDataFeedElement.getTime();
        versatileData.connectionHash = this.hashPairs[backtestDataFeedElement.getHashPairIndex()].connectionHash;
        versatileData.symbolHash = this.hashPairs[backtestDataFeedElement.getHashPairIndex()].symbolHash;
        if (backtestDataFeedElement.getType() == 2) {
            versatileData.type = 2;
            versatileData.open = backtestDataFeedElement.getOpen();
            versatileData.high = backtestDataFeedElement.getHigh();
            versatileData.low = backtestDataFeedElement.getLow();
            versatileData.close = backtestDataFeedElement.getClose();
            versatileData.volume = backtestDataFeedElement.getVolume();
            versatileData.sessionStartTime = backtestDataFeedElement.getSessionStartTime();
        } else {
            versatileData.type = 1;
            versatileData.bid = backtestDataFeedElement.getBid();
            versatileData.ask = backtestDataFeedElement.getAsk();
            versatileData.volume = backtestDataFeedElement.getVolume();
            versatileData.sessionStartTime = backtestDataFeedElement.getSessionStartTime();
        }
        ++this.index;
        return versatileData;
    }

    @Override
    public long size() {
        return this.dataCount;
    }

    @Override
    public void afterProduce() {
    }

    @Override
    public void setParams(boolean bl, int n) {
    }

    @Override
    public HashPair[] getHashPairs() {
        return null;
    }

    @Override
    public void destroy() {
        this.data = null;
    }

    @Override
    public void setMarketData(MarketData[] marketDataArray) {
    }

    @Override
    public MarketData[] getMarketData() {
        return null;
    }

    @Override
    public long freeIfInMemory() {
        return 0L;
    }
}

