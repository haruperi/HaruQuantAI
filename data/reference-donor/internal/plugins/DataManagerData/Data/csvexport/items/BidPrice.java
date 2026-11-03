/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class BidPrice
extends AbstractItem {
    public static final String Key = "Bid";
    public static final String Header = "Bid";

    public BidPrice() {
        super("Bid price", "Bid", "Bid");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.d(data.bid, decimals);
    }

    @Override
    public AbstractItem clone() {
        return new BidPrice();
    }
}

