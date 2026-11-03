/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class Symbol
extends AbstractItem {
    public static final String Key = "Symbol";
    public static final String Header = "Symbol";

    public Symbol() {
        super("Symbol", "Symbol", "Symbol");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return symbol;
    }

    @Override
    public AbstractItem clone() {
        return new Symbol();
    }
}

