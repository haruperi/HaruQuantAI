/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class TimeCol
extends DefaultCol {
    public static final String NAME = "Time";

    public TimeCol() {
        super(NAME, "TIME");
    }

    @Override
    public int getType() {
        return 7;
    }

    @Override
    public int getDataType() {
        return 10;
    }
}

