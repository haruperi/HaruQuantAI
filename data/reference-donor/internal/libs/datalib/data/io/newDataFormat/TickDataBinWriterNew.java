/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.newDataFormat;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.data.io.newDataFormat.DataBinWriterNew;
import com.strategyquant.datalib.data.io.newDataFormat.TickDataWriter;

public class TickDataBinWriterNew
extends DataBinWriterNew {
    TickDataWriter tickWriter = new TickDataWriter();

    TickDataBinWriterNew(String string) {
        super(string);
    }

    @Override
    public int getColumnsCount() {
        return 0;
    }

    @Override
    public void writeData(VersatileData versatileData) throws Exception {
        this.tickWriter.writeData(this.writer, this.modifyDataBeforeSave(versatileData, true));
    }

    @Override
    public void reset() {
        this.tickWriter.reset();
    }

    @Override
    public void overrideDecimals(int n) {
        this.tickWriter.overrideDecimals(n);
    }
}

