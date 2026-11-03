/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  org.joda.time.format.DateTimeFormat
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;
import org.joda.time.format.DateTimeFormat;

public class Time
extends AbstractItem {
    public static final String Key = "Time";
    public static final String Header = "Time";

    public Time() {
        super("Time", "Time", "Time");
        this.formatter = DateTimeFormat.forPattern((String)"HH:mm:ss");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.formatter.print(data.time);
    }

    @Override
    public AbstractItem clone() {
        return new Time();
    }

    @Override
    public void setFormat(String format) {
        this.formatter = DateTimeFormat.forPattern((String)format);
    }
}

