/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader
 *  com.strategyquant.datalib.data.io.newDataFormat.OhlcDataReader
 *  com.strategyquant.datalib.data.io.newDataFormat.OhlcDataWriter
 *  com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile
 *  com.strategyquant.datalib.data.io.newDataFormat.TickDataReader
 *  com.strategyquant.datalib.data.io.newDataFormat.TickDataWriter
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.IRandomAccessReader;
import com.strategyquant.datalib.data.io.newDataFormat.OhlcDataReader;
import com.strategyquant.datalib.data.io.newDataFormat.OhlcDataWriter;
import com.strategyquant.datalib.data.io.newDataFormat.RandomAccessReaderFile;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataReader;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataWriter;
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

public class LoadedDataHolderFileBDF
implements ILoadedDataHolder,
IFeedDataSaver {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedDataHolderFile");
    private static final int NUM_RECORDS = 200;
    private int index = 0;
    private TickDataWriter[] tickWriters = new TickDataWriter[10];
    private OhlcDataWriter[] ohlcWriters = new OhlcDataWriter[10];
    private TickDataReader[] tickReaders = new TickDataReader[10];
    private OhlcDataReader[] ohlcReaders = new OhlcDataReader[10];
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
    private MarketData[] marketDatas = null;

    public LoadedDataHolderFileBDF(int n) throws Exception {
        this.hash = n;
        this.fileName = TestfilesUtils.getTestdataFile(n);
        File file = new File(this.fileName);
        if (file.exists()) {
            if (file.length() < 100L) {
                file.delete();
            } else {
                this.openRar();
            }
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
            Log.error("Exception", (Throwable)fileNotFoundException);
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
            Log.error("Exception ", (Throwable)exception);
            exception.printStackTrace();
        }
    }

    @Override
    public ILoadedDataHolder cloneHolder() throws Exception {
        LoadedDataHolderFileBDF loadedDataHolderFileBDF = new LoadedDataHolderFileBDF(this.hash);
        loadedDataHolderFileBDF.fileName = this.fileName;
        loadedDataHolderFileBDF.index = 0;
        loadedDataHolderFileBDF.lastSessionStartTime = this.lastSessionStartTime;
        loadedDataHolderFileBDF.hashPairs = this.hashPairs;
        loadedDataHolderFileBDF.marketDatas = this.marketDatas;
        return loadedDataHolderFileBDF;
    }

    @Override
    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        if (!this.rar.dataRemaining()) {
            return null;
        }
        byte by = this.rar.readByte();
        int n = by >> 6;
        int n2 = by & 0xF;
        versatileData.type = (by & 0x30) >> 4;
        byte by2 = this.rar.readByte();
        versatileData.connectionHash = this.hashPairs[by2].connectionHash;
        versatileData.symbolHash = this.hashPairs[by2].symbolHash;
        versatileData.sessionStartTime = n == 0 ? (this.lastSessionStartTime = this.rar.readLong()) : this.lastSessionStartTime;
        int n3 = versatileData.connectionHash + versatileData.symbolHash;
        this.lastDecimals = n2;
        boolean bl = this.lastOHLC = versatileData.type == 2;
        if (versatileData.type == 1) {
            this.getTickReader(n3, n2).readData((IRandomAccessReader)this.rar, versatileData);
        } else {
            this.getOhlcReader(n3, n2).readData((IRandomAccessReader)this.rar, versatileData);
        }
        ++this.index;
        return versatileData;
    }

    @Override
    public long size() {
        return 0L;
    }

    @Override
    public void saveTick(VersatileData versatileData) throws Exception {
        byte by = (byte)this.decimals;
        by = (byte)(by | 16 * versatileData.type);
        boolean bl = this.lastSessionStartTime == versatileData.sessionStartTime;
        by = (byte)(by | 64 * (bl ? 1 : 0));
        this.byteBuffer.put(by);
        this.byteBuffer.put(this.getHashPairIndex(versatileData.connectionHash, versatileData.symbolHash));
        if (!bl) {
            this.lastSessionStartTime = versatileData.sessionStartTime;
            this.byteBuffer.putLong(versatileData.sessionStartTime);
        }
        if (this.isOhlc) {
            this.getOhlcWriter(this.decimals).putData(this.byteBuffer, versatileData);
        } else {
            this.getTickWriter(this.decimals).putData(this.byteBuffer, versatileData);
        }
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
                this.rar = null;
                this.inChannel.close();
            }
            catch (IOException iOException) {
                Log.error("Error closing Inchannel + ReadFile", (Throwable)iOException);
            }
        }
        if (this.rar != null) {
            try {
                this.rar.closeFile();
            }
            catch (IOException iOException) {
                Log.error("Error closing ReadFile", (Throwable)iOException);
            }
        }
    }

    @Override
    public void setParams(boolean bl, int n) {
        this.isOhlc = bl;
        this.decimals = n;
    }

    private TickDataWriter getTickWriter(int n) {
        if (n > 9) {
            throw new IllegalArgumentException("Decimals cannot be bigger than 9");
        }
        if (this.tickWriters[n] == null) {
            this.tickWriters[n] = new TickDataWriter(true);
        }
        return this.tickWriters[n];
    }

    private OhlcDataWriter getOhlcWriter(int n) {
        if (n > 9) {
            throw new IllegalArgumentException("Decimals cannot be bigger than 9");
        }
        if (this.ohlcWriters[n] == null) {
            this.ohlcWriters[n] = new OhlcDataWriter(true);
        }
        return this.ohlcWriters[n];
    }

    private TickDataReader getTickReader(int n, int n2) {
        if (n2 > 9) {
            throw new IllegalArgumentException("Decimals cannot be bigger than 9");
        }
        if (this.tickReaders[n2] == null) {
            this.tickReaders[n2] = new TickDataReader(true);
        }
        return this.tickReaders[n2];
    }

    private OhlcDataReader getOhlcReader(int n, int n2) {
        if (n2 > 9) {
            throw new IllegalArgumentException("Decimals cannot be bigger than 9");
        }
        if (this.ohlcReaders[n2] == null) {
            this.ohlcReaders[n2] = new OhlcDataReader(true);
        }
        return this.ohlcReaders[n2];
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
        this.marketDatas = marketDataArray;
    }

    @Override
    public MarketData[] getMarketData() {
        return this.marketDatas;
    }

    @Override
    public long freeIfInMemory() {
        return 0L;
    }

    public void close() throws IOException {
        if (this.rar != null) {
            this.rar.closeFile();
        }
        if (this.randAccessFile != null) {
            this.randAccessFile.close();
        }
    }
}

