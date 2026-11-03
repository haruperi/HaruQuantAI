/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class DateTimeCol
extends DefaultCol {
    public DateTimeCol() {
        super("Date & Time", "DATETIME");
    }

    @Override
    public int getType() {
        return 10;
    }

    @Override
    public int getDataType() {
        return 9;
    }
}

