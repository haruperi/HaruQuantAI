/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class AskCol
extends DefaultCol {
    public AskCol() {
        super("Ask", "ASK");
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public int getDataType() {
        return 2;
    }
}

