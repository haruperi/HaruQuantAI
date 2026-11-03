/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io.columns;

import com.strategyquant.datalib.data.io.columns.DefaultCol;

public class VolumeCol
extends DefaultCol {
    public VolumeCol() {
        super("Volume", "VOLUME");
    }

    @Override
    public int getType() {
        return 9;
    }

    @Override
    public int getDataType() {
        return 1;
    }
}

