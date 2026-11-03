/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class LowCol
extends DefaultCol {
    public LowCol() {
        super("Low", "LOW");
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public int getDataType() {
        return 6;
    }
}

