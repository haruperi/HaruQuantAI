/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.FuturesVersatileData;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.data.io.newDataFormat.FuturesDataWriter;
import java.io.IOException;
import java.io.RandomAccessFile;

public class FuturesDataBinWriterNew
extends DataBinWriterNew {
    private FuturesDataWriter futuresWriter = new FuturesDataWriter();
    private FuturesVersatileData modifiedVersatileData;

    public FuturesDataBinWriterNew(String string) {
        super(string);
    }

    @Override
    public int getColumnsCount() {
        return 8;
    }

    @Override
    public void writeData(VersatileData versatileData) throws Exception {
        this.futuresWriter.writeData(this.writer, this.modifyDataBeforeSave((FuturesVersatileData)versatileData, false));
    }

    protected FuturesVersatileData modifyDataBeforeSave(FuturesVersatileData futuresVersatileData, boolean bl) {
        if (!this.isCrypted()) {
            return futuresVersatileData;
        }
        if (bl) {
            this.modifiedVersatileData.ask = futuresVersatileData.ask + (double)this.modificators[0];
            this.modifiedVersatileData.bid = futuresVersatileData.bid + (double)this.modificators[1];
        } else {
            this.modifiedVersatileData.open = futuresVersatileData.open + (double)this.modificators[0];
            this.modifiedVersatileData.high = futuresVersatileData.high + (double)this.modificators[1];
            this.modifiedVersatileData.low = futuresVersatileData.low + (double)this.modificators[2];
            this.modifiedVersatileData.close = futuresVersatileData.close + (double)this.modificators[3];
        }
        this.modifiedVersatileData.time = futuresVersatileData.time + (long)this.timeModificator;
        this.modifiedVersatileData.volume = futuresVersatileData.volume + (double)this.modificators[0];
        this.modifiedVersatileData.openInterest = futuresVersatileData.openInterest + (double)this.modificators[0];
        return this.modifiedVersatileData;
    }

    @Override
    protected void writeModificatorsToHeader() throws Exception {
        super.writeModificatorsToHeader();
        if (this.isCrypted()) {
            this.modifiedVersatileData = new FuturesVersatileData();
        }
    }

    @Override
    public void reset() {
        this.futuresWriter.reset();
    }

    @Override
    public void close() throws Exception {
        super.close();
        this.updateCountInHeader();
    }

    private void updateCountInHeader() throws IOException {
        long l = this.futuresWriter.getSavedCount();
        RandomAccessFile randomAccessFile = new RandomAccessFile(this.getFileName(), "rw");
        long l2 = 2 + "4.2".length() + 2 + "ABCDEFGH".length() + 2 + "D".length();
        randomAccessFile.seek(l2);
        randomAccessFile.writeLong(l);
        randomAccessFile.close();
    }

    @Override
    public void overrideDecimals(int n) {
        this.futuresWriter.overrideDecimals(n);
    }
}

