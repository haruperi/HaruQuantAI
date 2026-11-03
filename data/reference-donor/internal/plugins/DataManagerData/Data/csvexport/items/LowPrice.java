/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class LowPrice
extends AbstractItem {
    public static final String Key = "Low";
    public static final String Header = "Low";

    public LowPrice() {
        super("Low price", "Low", "Low");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.d(data.low, decimals);
    }

    @Override
    public AbstractItem clone() {
        return new LowPrice();
    }
}

