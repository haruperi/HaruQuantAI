/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class HighCol
extends DefaultCol {
    public HighCol() {
        super("High", "HIGH");
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public int getDataType() {
        return 5;
    }
}

