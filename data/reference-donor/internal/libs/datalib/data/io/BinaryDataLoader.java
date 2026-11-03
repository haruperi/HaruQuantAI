/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.io.ICanSeek;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.lib.SQTime;
import java.io.File;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BinaryDataLoader
implements IDataLoader {
    public static final Logger Log = LoggerFactory.getLogger((String)"BinaryDataLoader");
    private String filePath;
    private DataBinReaderNew reader;
    private boolean eof = false;
    private int dataType;
    private int connectionHash;
    private int symbolHash;
    private ChartDef chartDef;
    private boolean dataInBuffer;
    private int specialId = -1;
    private long dateFrom;
    private DataInfo dataInfo;

    public BinaryDataLoader(String string, ChartDef chartDef, int n, DataInfo dataInfo) {
        this.filePath = string;
        this.connectionHash = chartDef.getConnectionHash();
        this.symbolHash = chartDef.getSymbolHash();
        this.chartDef = chartDef;
        this.dataType = n;
        this.dataInfo = dataInfo;
    }

    @Override
    public void open() throws Exception {
        File file = new File(this.filePath);
        if (!file.exists() || file.isDirectory()) {
            throw new Exception("BinaryDataLoader - Data file '" + this.filePath + "' doesn't exist!");
        }
        this.reader = DataBinReaderNew.getInstance(this.dataType, this.dataInfo.symbolInfo);
        this.reader.setFileName(this.filePath);
        this.reader.openFile();
        this.dataInBuffer = false;
        long l = System.currentTimeMillis();
        this.loadLinesUntilFromDate();
        long l2 = System.currentTimeMillis();
        Log.debug("BinaryDataLoader -  loadLinesUntilFromDate TOOK: " + (l2 - l) + " ms");
    }

    private void loadLinesUntilFromDate() throws Exception {
        boolean bl = false;
        this.eof = false;
        while (this.reader.readData()) {
            long l = this.reader.tickData.time;
            if (l < this.chartDef.getLoadedHistoryFrom()) continue;
            bl = true;
            this.dataInBuffer = true;
            this.dateFrom = l;
            Log.debug("History from: " + SQTime.toFullDateMinuteString((long)l));
            Log.debug("History to: " + SQTime.toFullDateMinuteString((long)this.chartDef.getHistoryTo()));
            break;
        }
        if (!bl) {
            this.eof = true;
        }
    }

    @Override
    public void close() throws Exception {
        if (this.reader != null) {
            this.reader.closeFile();
        }
    }

    @Override
    public boolean hasNextTick() throws Exception {
        if (this.reader == null) {
            throw new Exception("You have to call DataLoader.open() method first!");
        }
        if (this.eof) {
            return false;
        }
        if (this.dataInBuffer) {
            return true;
        }
        if (this.reader.readData()) {
            if (this.chartDef.getHistoryTo() > 0L && this.reader.tickData.time > this.chartDef.getHistoryTo()) {
                return false;
            }
            this.dataInBuffer = true;
            return true;
        }
        return false;
    }

    @Override
    public long nextTickTime() throws Exception {
        return this.reader.tickData.time;
    }

    @Override
    public void getNextTick(VersatileData versatileData) throws Exception {
        if (this.reader == null) {
            throw new Exception("You have to call DataLoader.open() method first!");
        }
        if (this.dataType == 1) {
            versatileData.set(2, this.reader.tickData.time, this.connectionHash, this.symbolHash, this.reader.tickData.open, this.reader.tickData.high, this.reader.tickData.low, this.reader.tickData.close, this.reader.tickData.volume);
        } else {
            versatileData.set(1, this.reader.tickData.time, this.connectionHash, this.symbolHash, this.reader.tickData.ask, this.reader.tickData.bid, this.reader.tickData.volume);
        }
        this.dataInBuffer = false;
    }

    @Override
    public boolean isOHLCData() {
        return this.dataType == 1;
    }

    @Override
    public long getDateFrom() {
        return this.dateFrom;
    }

    @Override
    public int getDecimalPlaces() {
        return this.dataInfo.decimals;
    }

    @Override
    public void seek(int n) throws Exception {
        if (this.reader instanceof ICanSeek) {
            ((ICanSeek)((Object)this.reader)).seek(n);
            this.dataInBuffer = false;
        }
    }

    @Override
    public long getTotalRecords() throws Exception {
        return this.reader.getTotalRecords();
    }

    @Override
    public String getDataFilePath() {
        return this.filePath;
    }

    @Override
    public boolean isCrypted() {
        return this.reader.isCrypted();
    }
}

