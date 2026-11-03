/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.FuturesVersatileData;
import com.strategyquant.datalib.data.io.ICanSeek;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.FuturesDataReader;
import java.io.EOFException;

public class FuturesDataBinReaderNew
extends DataBinReaderNew
implements ICanSeek {
    private int headerByteLength = -1;
    private long totalRecords = -1L;
    public final FuturesVersatileData tickData = new FuturesVersatileData();
    private FuturesDataReader futuresReader = new FuturesDataReader();

    @Override
    public int getColumnsCount() {
        return 8;
    }

    @Override
    public boolean readData() throws Exception {
        this.tickData.reset();
        if (!this.dataRemaining()) {
            return false;
        }
        try {
            this.futuresReader.readData(this.reader, this.tickData);
            this.fixData(this.tickData, false);
            return this.tickData.time > 0L;
        }
        catch (EOFException eOFException) {
            return false;
        }
    }

    @Override
    public void readHeader() throws Exception {
        int n = 6;
        String string = this.reader.readUTF();
        boolean bl = string.equals("4.1");
        boolean bl2 = string.equals("4.2");
        if (!bl && !bl2) {
            throw new IllegalStateException("Not supported version of file: " + string);
        }
        if (bl) {
            this.futuresReader.setVolumeConstant(100.0);
        }
        String string2 = this.reader.readUTF();
        String string3 = this.reader.readUTF();
        n += string.length() + string2.length() + string3.length();
        boolean bl3 = string2.equals("C");
        this.setCrypted(bl3);
        if (!string2.equals("D") && !bl3) {
            throw new Exception("File type is not data.");
        }
        this.totalRecords = this.reader.readLong();
        n += 8;
        int n2 = this.reader.readInt();
        n += 4;
        for (int i = 0; i < n2; ++i) {
            String string4 = this.reader.readUTF();
            this.reader.readInt();
            n += 2 + string4.length() + 4;
        }
        String string5 = this.reader.readUTF();
        this.headerByteLength = n += 2 + string5.length();
        if (!string5.equals("SnRbTs")) {
            throw new Exception("DAT file is damaged!");
        }
        this.headerByteLength += this.readModificators();
        this.futuresReader.setDataStartPosition(this.headerByteLength);
    }

    @Override
    public void seek(int n) throws Exception {
        this.futuresReader.seek(this.reader, n);
    }

    @Override
    public long getTotalRecords() throws Exception {
        if (this.totalRecords == -1L) {
            this.countTotalRecords();
        }
        return this.totalRecords;
    }

    private void countTotalRecords() throws Exception {
        this.seek(0);
        this.totalRecords = 0L;
        do {
            ++this.totalRecords;
        } while (this.readData());
        this.seek(0);
    }

    @Override
    public void overrideDecimals(int n) {
        this.futuresReader.overrideDecimals(n);
    }
}

