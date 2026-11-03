/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.backtest.IFeedDataSaver;
import com.strategyquant.tradinglib.backtest.ILoadedDataHolder;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.strategy.MarketData;
import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.io.RandomAccessFile;
import java.nio.ByteBuffer;
import java.nio.channels.FileChannel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedDataHolderFilePlain
implements ILoadedDataHolder,
IFeedDataSaver {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedDataHolderFile");
    private static final int NUM_RECORDS = 200;
    private int index = 0;
    final ByteBuffer byteBuffer = ByteBuffer.allocate(11400);
    private RandomAccessFile randAccessFile = null;
    private RandomAccessReaderFile rar;
    private FileChannel inChannel;
    private boolean isOhlc;
    private int decimals;
    private String fileName;
    private int hash;
    private long lastSessionStartTime = -1L;
    private HashPair[] hashPairs;
    private boolean lastOHLC;
    private int lastDecimals;
    private boolean loaded = false;

    public LoadedDataHolderFilePlain(int n) throws Exception {
        this.hash = n;
        this.fileName = TestfilesUtils.getTestdataFile(n);
        File file = new File(this.fileName);
        if (file.exists()) {
            this.openRar();
        }
    }

    private void openRar() throws Exception {
        this.rar = new RandomAccessReaderFile(this.fileName);
        this.rar.openFile();
        this.lastSessionStartTime = -1L;
        this.loadHeader();
    }

    private void loadHeader() throws Exception {
        int n;
        if (!this.rar.dataRemaining()) {
            throw new Exception(L.t((String)"No data remaining in loading header!", (Object[])new Object[0]));
        }
        int n2 = this.rar.readByte();
        this.hashPairs = new HashPair[n2];
        for (n = 0; n < n2; ++n) {
            HashPair hashPair = new HashPair();
            hashPair.connectionHash = this.rar.readInt();
            hashPair.symbolHash = this.rar.readInt();
            this.hashPairs[n] = hashPair;
        }
        n = this.rar.readInt();
        if (n != 123456789) {
            throw new Exception(L.t((String)"Incorrect file header!", (Object[])new Object[0]));
        }
        this.loaded = true;
    }

    @Override
    public void beforeSave(HashPair[] hashPairArray) {
        File file = new File(this.fileName);
        try {
            this.randAccessFile = new RandomAccessFile(file, "rw");
            this.lastSessionStartTime = -1L;
            this.hashPairs = hashPairArray;
            this.saveHeader();
        }
        catch (FileNotFoundException fileNotFoundException) {
            fileNotFoundException.printStackTrace();
        }
    }

    private void saveHeader() {
        this.byteBuffer.put((byte)this.hashPairs.length);
        for (HashPair hashPair : this.hashPairs) {
            this.byteBuffer.putInt(hashPair.connectionHash);
            this.byteBuffer.putInt(hashPair.symbolHash);
        }
        this.byteBuffer.putInt(123456789);
    }

    @Override
    public void afterSave() {
        try {
            if (this.byteBuffer.position() > 0) {
                this.byteBuffer.flip();
                this.randAccessFile.getChannel().write(this.byteBuffer);
                this.byteBuffer.clear();
            }
            this.randAccessFile.close();
            this.openRar();
            this.loaded = true;
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
    }

    @Override
    public ILoadedDataHolder cloneHolder() throws Exception {
        LoadedDataHolderFilePlain loadedDataHolderFilePlain = new LoadedDataHolderFilePlain(this.hash);
        loadedDataHolderFilePlain.fileName = this.fileName;
        loadedDataHolderFilePlain.index = 0;
        loadedDataHolderFilePlain.lastSessionStartTime = this.lastSessionStartTime;
        loadedDataHolderFilePlain.hashPairs = this.hashPairs;
        return loadedDataHolderFilePlain;
    }

    @Override
    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        if (!this.rar.dataRemaining()) {
            return null;
        }
        versatileData.type = this.rar.readInt();
        byte by = this.rar.readByte();
        versatileData.connectionHash = this.hashPairs[by].connectionHash;
        versatileData.symbolHash = this.hashPairs[by].symbolHash;
        versatileData.sessionStartTime = this.rar.readLong();
        versatileData.time = this.rar.readLong();
        versatileData.ask = this.rar.readDouble();
        versatileData.bid = this.rar.readDouble();
        versatileData.volume = this.rar.readDouble();
        ++this.index;
        return versatileData;
    }

    @Override
    public long size() {
        return 0L;
    }

    @Override
    public void saveTick(VersatileData versatileData) throws Exception {
        this.byteBuffer.putInt(versatileData.type);
        this.byteBuffer.put(this.getHashPairIndex(versatileData.connectionHash, versatileData.symbolHash));
        this.byteBuffer.putLong(versatileData.sessionStartTime);
        this.byteBuffer.putLong(versatileData.time);
        this.byteBuffer.putDouble(versatileData.ask);
        this.byteBuffer.putDouble(versatileData.bid);
        this.byteBuffer.putDouble(versatileData.volume);
        if (this.byteBuffer.remaining() < 100) {
            this.byteBuffer.flip();
            this.randAccessFile.getChannel().write(this.byteBuffer);
            this.byteBuffer.clear();
        }
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
        if (this.inChannel != null) {
            try {
                this.rar.closeFile();
                this.inChannel.close();
            }
            catch (IOException iOException) {
                iOException.printStackTrace();
            }
        }
    }

    @Override
    public void setParams(boolean bl, int n) {
        this.isOhlc = bl;
        this.decimals = n;
    }

    @Override
    public HashPair[] getHashPairs() {
        return this.hashPairs;
    }

    public boolean isOHLC() {
        return this.lastOHLC;
    }

    public int getDecimals() {
        return this.lastDecimals;
    }

    public boolean isLoaded() {
        return this.loaded;
    }

    @Override
    public void destroy() {
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

