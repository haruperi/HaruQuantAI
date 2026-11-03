/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class CustomValue
extends DefaultCol {
    public CustomValue(int n) {
        super("Value" + n, "Value" + n);
    }

    @Override
    public int getType() {
        return 5;
    }

    @Override
    public int getDataType() {
        return 9999;
    }
}

