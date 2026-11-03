/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.data.io.newDataFormat.OhlcDataWriter;
import java.io.IOException;
import java.io.RandomAccessFile;

public class OhlcDataBinWriterNew
extends DataBinWriterNew {
    private OhlcDataWriter ohlcWriter = new OhlcDataWriter();

    OhlcDataBinWriterNew(String string) {
        super(string);
    }

    @Override
    public int getColumnsCount() {
        return 8;
    }

    @Override
    public void writeData(VersatileData versatileData) throws Exception {
        this.ohlcWriter.writeData(this.writer, this.modifyDataBeforeSave(versatileData, false));
    }

    @Override
    public void reset() {
        this.ohlcWriter.reset();
    }

    @Override
    public void close() throws Exception {
        super.close();
        this.updateCountInHeader();
    }

    private void updateCountInHeader() throws IOException {
        long l = this.ohlcWriter.getSavedCount();
        RandomAccessFile randomAccessFile = new RandomAccessFile(this.getFileName(), "rw");
        long l2 = 2 + "4.2".length() + 2 + "ABCDEFGH".length() + 2 + "D".length();
        randomAccessFile.seek(l2);
        randomAccessFile.writeLong(l);
        randomAccessFile.close();
    }

    @Override
    public void overrideDecimals(int n) {
        this.ohlcWriter.overrideDecimals(n);
    }
}

