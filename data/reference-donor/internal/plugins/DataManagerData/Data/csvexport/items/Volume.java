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

public class Volume
extends AbstractItem {
    public static final String Key = "Volume";
    public static final String Header = "Volume";

    public Volume() {
        super("Volume", "Volume", "Volume");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        if (data.volume > 1.0) {
            return SQUtils.roundLong((double)(this.count > 1 ? data.volume / (double)this.count : data.volume)) + "";
        }
        return "1";
    }

    @Override
    public AbstractItem clone() {
        return new Volume();
    }
}

