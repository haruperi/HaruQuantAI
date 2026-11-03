/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.io.DataBinWriter;
import com.strategyquant.datalib.data.io.VersatileData;
import java.io.IOException;

public class OhlcDataBinWriter
extends DataBinWriter {
    public OhlcDataBinWriter(String string) {
        super(string);
    }

    public OhlcDataBinWriter(String string, InstrumentInfo instrumentInfo, String string2) {
        super(string);
        this.setParams(null, instrumentInfo, null);
        String string3 = instrumentInfo.filename == null || instrumentInfo.filename == "" ? instrumentInfo.instrument : instrumentInfo.filename;
        this.setFileName(string + "/" + string3 + "_" + string2 + ".dat");
    }

    @Override
    public int getColumnsCount() {
        return 8;
    }

    @Override
    protected void writeHeader() throws Exception {
        this.writer.writeUTF("4.0");
        this.writer.writeUTF("D");
        this.writer.writeUTF("ABCDEFGH");
        this.writer.writeInt(this.getColumnsCount());
        for (int i = 0; i < this.getColumnsCount(); ++i) {
            this.writer.writeUTF("_");
            this.writer.writeInt(0);
        }
        this.writer.writeUTF("SnRbTs");
    }

    @Override
    public void writeData(VersatileData versatileData) throws IOException {
        this.write(versatileData.time, versatileData.open, versatileData.high, versatileData.low, versatileData.close, versatileData.volume);
    }

    private void write(long l, double d, double d2, double d3, double d4, double d5) throws IOException {
        this.writer.writeLong(l);
        this.writer.writeDouble(d);
        this.writer.writeDouble(d2);
        this.writer.writeDouble(d3);
        this.writer.writeDouble(d4);
        this.writer.writeDouble(d5);
    }
}

