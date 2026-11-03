/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;

public class TextItem
extends AbstractItem {
    public TextItem() {
        super("TextItem", "TextItem", "TextItem");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.value;
    }

    @Override
    public AbstractItem clone() {
        return new TextItem();
    }
}

