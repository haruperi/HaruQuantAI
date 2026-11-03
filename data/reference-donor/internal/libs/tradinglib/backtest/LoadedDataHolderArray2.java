/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.backtest.DataLoadStats;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.backtest.ILoadedDataHolder;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.LoadedDataHolderFileBDF;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.File;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedDataHolderArray2
implements ILoadedDataHolder {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedDataHolderArray");
    private VersatileData[] dataArray = null;
    private int hash;
    private long lastSessionStartTime = -1L;
    private HashPair[] hashPairs;
    private String fileName;
    private int totalRecords = 0;
    private long allocatedSize = 0L;
    private int readRecord = 0;
    private boolean isOhlc;
    private MarketData[] marketDatas = null;
    private long newAllocatedSize;

    public LoadedDataHolderArray2(int n, LoadedDataHolderFileBDF loadedDataHolderFileBDF, DataLoadStats dataLoadStats, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        this.hash = n;
        this.hashPairs = loadedDataHolderFileBDF.getHashPairs();
        this.fileName = TestfilesUtils.getTestdataFile(n, true);
        File file = new File(this.fileName);
        if (!file.exists()) {
            throw new Exception(L.t((String)"File %s doesnot exist!", (Object[])new Object[]{this.fileName}));
        }
        try {
            this.loadFileToArray(loadedDataHolderFileBDF, dataLoadStats, file.length(), loadDataProgressEngine);
        }
        catch (OutOfMemoryError outOfMemoryError) {
            Log.info("Cannot allocate enough memory for offheap data! Already alocated: {}, new size that failed: {}", (Object)this.allocatedSize, (Object)this.newAllocatedSize);
            if (loadDataProgressEngine != null) {
                loadDataProgressEngine.printToLog(L.t((String)"Cannot load data into memory, keeping it in file", (Object[])new Object[0]));
            }
            this.freeAlocatedMemory();
            throw outOfMemoryError;
        }
    }

    private void freeAlocatedMemory() {
        this.dataArray = null;
    }

    public LoadedDataHolderArray2(int n, VersatileData[] versatileDataArray) {
        this.hash = n;
    }

    private void loadFileToArray(LoadedDataHolderFileBDF loadedDataHolderFileBDF, DataLoadStats dataLoadStats, long l, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        long l2 = System.currentTimeMillis();
        long l3 = l / 10L;
        this.dataArray = new VersatileData[(int)l3];
        VersatileData versatileData = new VersatileData();
        this.totalRecords = 0;
        long l4 = 0L;
        while ((versatileData = loadedDataHolderFileBDF.getNextTick(versatileData)) != null) {
            this.setParams(versatileData.type == 2, 0);
            this._saveTick(versatileData);
            if (versatileData.time <= l4) continue;
            l4 = versatileData.time;
        }
        dataLoadStats.loadingTime = System.currentTimeMillis() - l2;
        Log.info("Data loaded from file to array in {} ms., records: {}", (Object)dataLoadStats.loadingTime, (Object)this.totalRecords);
        Log.info("Latest time: {}", (Object)SQTime.toDateMinuteString((long)l4));
        if (Log.isDebugEnabled()) {
            Log.debug("Data loaded from file to array in {} ms., records: {}", (Object)dataLoadStats.loadingTime, (Object)this.totalRecords);
            Log.debug("Latest time: {}", (Object)SQTime.toDateMinuteString((long)l4));
        }
        if (loadDataProgressEngine != null) {
            double d = (double)dataLoadStats.loadingTime / 1000.0;
            loadDataProgressEngine.printToLog(L.t((String)"Loaded to memory in %.4f s., memory: %s", (Object[])new Object[]{d, SQUtils.formatBytesToHumanFormat((long)this.allocatedSize)}));
        }
    }

    @Override
    public ILoadedDataHolder cloneHolder() throws Exception {
        LoadedDataHolderArray2 loadedDataHolderArray2 = new LoadedDataHolderArray2(this.hash, this.dataArray);
        loadedDataHolderArray2.dataArray = this.dataArray;
        loadedDataHolderArray2.lastSessionStartTime = this.lastSessionStartTime;
        loadedDataHolderArray2.hashPairs = this.hashPairs;
        loadedDataHolderArray2.totalRecords = this.totalRecords;
        loadedDataHolderArray2.allocatedSize = this.allocatedSize;
        loadedDataHolderArray2.readRecord = 0;
        loadedDataHolderArray2.marketDatas = this.marketDatas;
        return loadedDataHolderArray2;
    }

    @Override
    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        if (this.readRecord >= this.totalRecords) {
            return null;
        }
        ++this.readRecord;
        return this.dataArray[this.readRecord - 1];
    }

    @Override
    public long size() {
        return this.totalRecords;
    }

    @Override
    public void saveTick(VersatileData versatileData) throws Exception {
        throw new Exception(L.t((String)"Not implemented here!", (Object[])new Object[0]));
    }

    public void _saveTick(VersatileData versatileData) throws Exception {
        VersatileData versatileData2 = new VersatileData();
        versatileData2.copyFrom(versatileData);
        if (this.totalRecords >= this.dataArray.length) {
            throw new Exception(L.t((String)"Records bigger than allocated array: %d >= %d ", (Object[])new Object[]{this.totalRecords, this.dataArray.length}));
        }
        this.dataArray[this.totalRecords] = versatileData2;
        ++this.totalRecords;
    }

    @Override
    public void afterProduce() {
    }

    @Override
    public void setParams(boolean bl, int n) {
        this.isOhlc = bl;
    }

    @Override
    public HashPair[] getHashPairs() {
        return this.hashPairs;
    }

    @Override
    public void destroy() {
        this.dataArray = null;
    }

    @Override
    public void setMarketData(MarketData[] marketDataArray) {
        this.marketDatas = marketDataArray;
    }

    @Override
    public MarketData[] getMarketData() {
        return this.marketDatas;
    }

    @Override
    public void beforeSave(HashPair[] hashPairArray) throws Exception {
        throw new Exception(L.t((String)"Not implemented here!", (Object[])new Object[0]));
    }

    @Override
    public void afterSave() throws Exception {
        throw new Exception(L.t((String)"Not implemented here!", (Object[])new Object[0]));
    }

    @Override
    public long freeIfInMemory() {
        return 0L;
    }
}

