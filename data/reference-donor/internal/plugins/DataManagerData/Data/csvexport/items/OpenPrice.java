/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class OpenPrice
extends AbstractItem {
    public static final String Key = "Open";
    public static final String Header = "Open";

    public OpenPrice() {
        super("Open price", "Open", "Open");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.d(data.open, decimals);
    }

    @Override
    public AbstractItem clone() {
        return new OpenPrice();
    }
}

