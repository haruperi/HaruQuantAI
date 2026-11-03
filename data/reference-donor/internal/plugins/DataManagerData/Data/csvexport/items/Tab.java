/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class Tab
extends AbstractItem {
    public static final String Key = "Tab";
    public static final String Header = "[Tab]";

    public Tab() {
        super(Key, Key, Header);
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return "\t";
    }

    @Override
    public AbstractItem clone() {
        return new Tab();
    }
}

