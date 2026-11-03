/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.newDataFormat.DataBinReaderNew;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataReader;
import java.io.EOFException;

public class TickDataBinReaderNew
extends DataBinReaderNew {
    private TickDataReader tickReader = new TickDataReader();
    private long totalRecords = -1L;
    private int headerByteLength;

    TickDataBinReaderNew() {
    }

    @Override
    public int getColumnsCount() {
        return 0;
    }

    @Override
    public boolean readData() throws Exception {
        this.tickData.reset();
        if (!this.dataRemaining()) {
            return false;
        }
        try {
            this.tickReader.readData(this.reader, this.tickData);
            this.fixData(this.tickData, true);
            return true;
        }
        catch (EOFException eOFException) {
            return false;
        }
    }

    @Override
    public void readHeader() throws Exception {
        try {
            int n = 6;
            String string = this.reader.readUTF();
            if (!string.equals("4.2")) {
                throw new IllegalStateException("Not supported version of file: " + string);
            }
            String string2 = this.reader.readUTF();
            String string3 = this.reader.readUTF();
            n += string.length() + string2.length() + string3.length();
            boolean bl = string2.equals("C");
            this.setCrypted(bl);
            if (!string2.equals("D") && !bl) {
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
            this.tickReader.setDataStartPosition(this.headerByteLength);
        }
        catch (Exception exception) {
            this.tickReader.setDataStartPosition(0L);
            this.tickReader.setVolumeConstant(100.0);
        }
    }

    @Override
    public long getTotalRecords() throws Exception {
        return this.totalRecords;
    }

    @Override
    public void seek(int n) throws Exception {
        this.tickReader.seek(this.reader, n);
    }

    @Override
    public void overrideDecimals(int n) {
        this.tickReader.overrideDecimals(n);
    }
}

