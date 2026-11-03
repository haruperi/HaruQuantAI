/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class Comma
extends AbstractItem {
    public static final String Key = ",";
    public static final String Header = ",";

    public Comma() {
        super("Comma", ",", ",");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return ",";
    }

    @Override
    public AbstractItem clone() {
        return new Comma();
    }
}

