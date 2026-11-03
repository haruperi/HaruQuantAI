/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class Spread
extends AbstractItem {
    public static final String Key = "Spread";
    public static final String Header = "Spread";

    public Spread() {
        super("Spread", "Spread", "Spread");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        double spread = Math.abs(data.ask - data.bid);
        return String.valueOf(SQUtils.round((double)spread, (int)decimals));
    }

    @Override
    public AbstractItem clone() {
        return new Spread();
    }
}

