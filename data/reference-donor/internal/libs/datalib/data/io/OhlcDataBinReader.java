/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.DataBinReader;
import java.io.EOFException;

public class OhlcDataBinReader
extends DataBinReader {
    private boolean version4Format = false;
    private int headerByteLength = -1;
    private int dataByteLength = 44;

    @Override
    public int getColumnsCount() {
        return 8;
    }

    @Override
    public boolean readData() throws Exception {
        this.tickData.reset();
        try {
            this.tickData.time = this.reader.readLong();
            this.tickData.open = this.reader.readDouble();
            this.tickData.high = this.reader.readDouble();
            this.tickData.low = this.reader.readDouble();
            this.tickData.close = this.reader.readDouble();
            this.tickData.volume = this.reader.readDouble();
            return true;
        }
        catch (EOFException eOFException) {
            return false;
        }
    }

    @Override
    public void readHeader() throws Exception {
        int n = 0;
        String string = this.reader.readUTF();
        String string2 = this.reader.readUTF();
        String string3 = this.reader.readUTF();
        n += string.length() + string2.length() + string3.length();
        if (string.equalsIgnoreCase("4.0")) {
            this.version4Format = true;
        }
        if (!string2.equals("D")) {
            throw new Exception("File type is not data.");
        }
        int n2 = this.reader.readInt();
        n += 4;
        for (int i = 0; i < n2; ++i) {
            String string4 = this.reader.readUTF();
            int n3 = this.reader.readInt();
            n += string4.length() + 4;
        }
        String string5 = this.reader.readUTF();
        this.headerByteLength = n += string5.length();
        if (!string5.equals("SnRbTs")) {
            throw new Exception("DAT file is damaged!");
        }
    }
}

