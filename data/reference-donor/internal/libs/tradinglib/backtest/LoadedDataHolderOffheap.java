/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.MemoryInfo
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.memory.OffHeapMemory
 *  com.strategyquant.lib.offheap.IOffHeapCallback
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.MemoryInfo;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.memory.OffHeapMemory;
import com.strategyquant.lib.offheap.IOffHeapCallback;
import com.strategyquant.tradinglib.backtest.DataLoadStats;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.backtest.ILoadedDataHolder;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.LoadedDataHolderFileBDF;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.File;
import java.lang.management.MemoryMXBean;
import java.lang.management.MemoryUsage;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedDataHolderOffheap
implements ILoadedDataHolder {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedDataHolderOffheap");
    protected static final int MEGABYTE = 0x100000;
    private long address = -2L;
    private int hash;
    private long lastSessionStartTime = -1L;
    private boolean lastOHLC;
    private HashPair[] hashPairs;
    private String fileName;
    private int records = 0;
    private long recordsSize = 0L;
    private long allocatedSize = 0L;
    private long readRecordSize = 0L;
    private boolean isOhlc;
    private MarketData[] marketDatas = null;
    private long newAllocatedSize;
    private IOffHeapCallback offheapCallback;

    public LoadedDataHolderOffheap(int n, LoadedDataHolderFileBDF loadedDataHolderFileBDF, DataLoadStats dataLoadStats, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        this.hash = n;
        this.hashPairs = loadedDataHolderFileBDF.getHashPairs();
        this.offheapCallback = new IOffHeapCallback(){

            public void freeOffHeapMemory(boolean bl) {
                throw new IllegalArgumentException("Not yet implemented!");
            }

            public String getIdentification() {
                return "LoadedDataHolderOffheap";
            }
        };
        this.fileName = TestfilesUtils.getTestdataFile(n);
        File file = new File(this.fileName);
        if (!file.exists()) {
            throw new Exception(L.t((String)"File %s does not exist!", (Object[])new Object[]{this.fileName}));
        }
        try {
            this.loadFileToOffheapMemory(loadedDataHolderFileBDF, dataLoadStats, file.length(), loadDataProgressEngine);
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
        Log.info("Deallocating LoadedDataHolderOffheap, stack: {}", (Object)SQUtils.getStackTrace());
        OffHeapMemory.deallocate((IOffHeapCallback)this.offheapCallback, (long)this.address);
    }

    public LoadedDataHolderOffheap(int n, long l) {
        this.hash = n;
    }

    private void loadFileToOffheapMemory(LoadedDataHolderFileBDF loadedDataHolderFileBDF, DataLoadStats dataLoadStats, long l, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        long l2 = System.currentTimeMillis();
        long l3 = l / 10L;
        long l4 = l3 * 30L;
        this.address = OffHeapMemory.allocate((IOffHeapCallback)this.offheapCallback, (long)l4);
        this.allocatedSize = l4;
        VersatileData versatileData = new VersatileData();
        this.records = 0;
        long l5 = 0L;
        while ((versatileData = loadedDataHolderFileBDF.getNextTick(versatileData)) != null) {
            this.setParams(versatileData.type == 2, 0);
            this._saveTick(versatileData);
            if (versatileData.time <= l5) continue;
            l5 = versatileData.time;
        }
        dataLoadStats.loadingTime = System.currentTimeMillis() - l2;
        Log.debug("Data loaded from file to offheap memory in {} ms., records: {}, recordsSize: {}, allocatedSize: {}", new Object[]{dataLoadStats.loadingTime, this.records, this.recordsSize, this.allocatedSize});
        if (Log.isDebugEnabled()) {
            Log.debug("Latest time: {}", (Object)SQTime.toDateMinuteString((long)l5));
        }
        if (loadDataProgressEngine != null) {
            double d = (double)dataLoadStats.loadingTime / 1000.0;
            loadDataProgressEngine.printToLog(L.t((String)"Loaded to memory in %.4f s., memory: %s", (Object[])new Object[]{d, SQUtils.formatBytesToHumanFormat((long)this.allocatedSize)}));
        }
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
    public ILoadedDataHolder cloneHolder() throws Exception {
        LoadedDataHolderOffheap loadedDataHolderOffheap = new LoadedDataHolderOffheap(this.hash, this.address);
        this.checkOffHeap();
        loadedDataHolderOffheap.address = this.address;
        loadedDataHolderOffheap.lastSessionStartTime = this.lastSessionStartTime;
        loadedDataHolderOffheap.hashPairs = this.hashPairs;
        loadedDataHolderOffheap.address = this.address;
        loadedDataHolderOffheap.records = this.records;
        loadedDataHolderOffheap.recordsSize = this.recordsSize;
        loadedDataHolderOffheap.allocatedSize = this.allocatedSize;
        loadedDataHolderOffheap.readRecordSize = 0L;
        loadedDataHolderOffheap.marketDatas = this.marketDatas;
        loadedDataHolderOffheap.offheapCallback = this.offheapCallback;
        return loadedDataHolderOffheap;
    }

    @Override
    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        if (this.readRecordSize >= this.recordsSize) {
            return null;
        }
        byte by = this.getByte();
        int n = by >> 6;
        versatileData.type = (by & 0x30) >> 4;
        byte by2 = this.getByte();
        versatileData.connectionHash = this.hashPairs[by2].connectionHash;
        versatileData.symbolHash = this.hashPairs[by2].symbolHash;
        versatileData.sessionStartTime = n == 0 ? (this.lastSessionStartTime = this.getLong()) : this.lastSessionStartTime;
        boolean bl = this.lastOHLC = versatileData.type == 2;
        if (versatileData.type == 1) {
            this.readTickData(versatileData);
        } else {
            this.readOHLCData(versatileData);
        }
        ++this.records;
        return versatileData;
    }

    private void readTickData(VersatileData versatileData) {
        versatileData.time = this.getLong();
        versatileData.bid = this.getDouble();
        versatileData.ask = this.getDouble();
        versatileData.volume = this.getDouble();
    }

    private void readOHLCData(VersatileData versatileData) {
        versatileData.time = this.getLong();
        versatileData.open = this.getDouble();
        versatileData.high = this.getDouble();
        versatileData.low = this.getDouble();
        versatileData.close = this.getDouble();
        versatileData.volume = this.getDouble();
    }

    @Override
    public long size() {
        return this.recordsSize;
    }

    @Override
    public void saveTick(VersatileData versatileData) throws Exception {
        throw new Exception("Not implemented here!");
    }

    private void _saveTick(VersatileData versatileData) throws Exception {
        byte by = 0;
        by = (byte)(by | 16 * versatileData.type);
        boolean bl = this.lastSessionStartTime == versatileData.sessionStartTime;
        by = (byte)(by | 64 * (bl ? 1 : 0));
        this.putByte(by);
        this.putByte(this.getHashPairIndex(versatileData.connectionHash, versatileData.symbolHash));
        if (!bl) {
            this.lastSessionStartTime = versatileData.sessionStartTime;
            this.putLong(versatileData.sessionStartTime);
        }
        if (this.isOhlc) {
            this.saveOHLCData(versatileData);
        } else {
            this.saveTickData(versatileData);
        }
        ++this.records;
    }

    private void saveTickData(VersatileData versatileData) {
        this.putLong(versatileData.time);
        this.putDouble(versatileData.bid);
        this.putDouble(versatileData.ask);
        this.putDouble(versatileData.volume);
    }

    private void saveOHLCData(VersatileData versatileData) {
        this.putLong(versatileData.time);
        this.putDouble(versatileData.open);
        this.putDouble(versatileData.high);
        this.putDouble(versatileData.low);
        this.putDouble(versatileData.close);
        this.putDouble(versatileData.volume);
    }

    private void putByte(byte by) {
        this.checkAllocatedSize();
        OffHeapMemory.putByte((long)(this.address + this.recordsSize), (byte)by);
        ++this.recordsSize;
    }

    private void putLong(long l) {
        this.checkAllocatedSize();
        OffHeapMemory.putLong((long)(this.address + this.recordsSize), (long)l);
        this.recordsSize += 8L;
    }

    private void putDouble(double d) {
        this.checkAllocatedSize();
        OffHeapMemory.putDouble((long)(this.address + this.recordsSize), (double)d);
        this.recordsSize += 8L;
    }

    private void checkAllocatedSize() {
        if (this.recordsSize > this.allocatedSize - 100L) {
            this.newAllocatedSize = (long)((double)this.allocatedSize * 1.1);
            Log.debug("LoadedDataOfheap - Reallocating from {} to {}", (Object)this.allocatedSize, (Object)this.newAllocatedSize);
            this.address = OffHeapMemory.reallocate((IOffHeapCallback)this.offheapCallback, (long)this.address, (long)this.newAllocatedSize);
            this.allocatedSize = this.newAllocatedSize;
        }
    }

    private byte getByte() {
        byte by = OffHeapMemory.getByte((long)(this.address + this.readRecordSize));
        ++this.readRecordSize;
        return by;
    }

    private long getLong() {
        long l = OffHeapMemory.getLong((long)(this.address + this.readRecordSize));
        this.readRecordSize += 8L;
        return l;
    }

    private double getDouble() {
        double d = OffHeapMemory.getDouble((long)(this.address + this.readRecordSize));
        this.readRecordSize += 8L;
        return d;
    }

    private byte getHashPairIndex(int n, int n2) throws Exception {
        for (byte by = 0; by < this.hashPairs.length; by = (byte)((byte)(by + 1))) {
            if (this.hashPairs[by].connectionHash != n || this.hashPairs[by].symbolHash != n2) continue;
            return by;
        }
        throw new Exception(L.t((String)"HashPair for %d / %d was not found!", (Object[])new Object[]{n, n2}));
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
        Log.info("Destroying LoadedDataHolderOffheap, stack: {}", (Object)SQUtils.getStackTrace());
        OffHeapMemory.deallocate((IOffHeapCallback)this.offheapCallback, (long)this.address);
        this.address = -1L;
    }

    public void checkOffHeap() {
        if (this.address < 0L) {
            OffHeapMemory.throwMemoryException((long)this.address);
        }
    }

    @Override
    public void setMarketData(MarketData[] marketDataArray) {
        this.marketDatas = marketDataArray;
    }

    @Override
    public MarketData[] getMarketData() {
        return this.marketDatas;
    }

    public static boolean isEnoughMemory(int n, MemoryMXBean memoryMXBean) {
        String string = TestfilesUtils.getTestdataFile(n, false);
        File file = new File(string);
        if (!file.exists()) {
            return true;
        }
        long l = file.length() / 10L;
        long l2 = l * 30L / 0x100000L;
        MemoryUsage memoryUsage = memoryMXBean.getHeapMemoryUsage();
        long l3 = memoryUsage.getMax() / 0x100000L;
        MemoryInfo memoryInfo = new MemoryInfo();
        OffHeapMemory.getInfo((MemoryInfo)memoryInfo);
        long l4 = memoryInfo.allocatedMemory / 0x100000L;
        long l5 = memoryUsage.getCommitted() / 0x100000L;
        long l6 = l3 - (l4 + l5);
        return !((double)l2 > (double)l6 * 0.7);
    }

    @Override
    public long freeIfInMemory() {
        Log.info("freeIfInMemory LoadedDataHolderOffheap, stack: {}", (Object)SQUtils.getStackTrace());
        OffHeapMemory.deallocate((IOffHeapCallback)this.offheapCallback, (long)this.address);
        this.address = -1L;
        return this.allocatedSize;
    }
}

