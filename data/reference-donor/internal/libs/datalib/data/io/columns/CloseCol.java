/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class CloseCol
extends DefaultCol {
    public static final String NAME = "Close";

    public CloseCol() {
        super(NAME, "CLOSE");
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public int getDataType() {
        return 7;
    }
}

