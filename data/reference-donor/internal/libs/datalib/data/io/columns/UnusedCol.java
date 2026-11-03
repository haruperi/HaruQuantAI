/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class UnusedCol
extends DefaultCol {
    public UnusedCol() {
        super("Unused", "UNUSED");
    }

    @Override
    public int getType() {
        return 8;
    }

    @Override
    public int getDataType() {
        return 10;
    }
}

