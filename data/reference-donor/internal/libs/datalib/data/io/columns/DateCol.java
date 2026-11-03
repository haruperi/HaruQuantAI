/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class DateCol
extends DefaultCol {
    public static final String NAME = "Date";

    public DateCol() {
        super(NAME, "DATE");
    }

    @Override
    public int getType() {
        return 6;
    }

    @Override
    public int getDataType() {
        return 9;
    }
}

