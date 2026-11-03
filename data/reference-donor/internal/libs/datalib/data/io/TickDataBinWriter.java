/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.DataBinWriter;
import com.strategyquant.datalib.data.io.VersatileData;
import java.io.IOException;

public class TickDataBinWriter
extends DataBinWriter {
    public TickDataBinWriter(String string) {
        super(string);
    }

    @Override
    public int getColumnsCount() {
        return 0;
    }

    @Override
    public void writeHeader() throws Exception {
    }

    @Override
    public void writeData(VersatileData versatileData) throws IOException {
        this.writer.writeLong(versatileData.time);
        this.writer.writeDouble(versatileData.ask);
        this.writer.writeDouble(versatileData.bid);
        this.writer.writeDouble(versatileData.volume);
    }
}

