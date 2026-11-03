/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class ClosePrice
extends AbstractItem {
    public static final String Key = "Close";
    public static final String Header = "Close";

    public ClosePrice() {
        super("Close price", "Close", "Close");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.d(data.close, decimals);
    }

    @Override
    public AbstractItem clone() {
        return new ClosePrice();
    }
}

