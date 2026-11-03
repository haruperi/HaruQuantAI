/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class AskPrice
extends AbstractItem {
    public static final String Key = "Ask";
    public static final String Header = "Ask";

    public AskPrice() {
        super("Ask price", "Ask", "Ask");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.d(data.ask, decimals);
    }

    @Override
    public AbstractItem clone() {
        return new AskPrice();
    }
}

