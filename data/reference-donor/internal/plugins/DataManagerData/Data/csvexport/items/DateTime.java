/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  org.joda.time.format.DateTimeFormat
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.DataManager.impl.Data.csvexport.items.AbstractItem;
import org.joda.time.format.DateTimeFormat;

public class DateTime
extends AbstractItem {
    public static final String Key = "DateTime";
    public static final String Header = "DateTime";

    public DateTime() {
        super("Date time", "DateTime", "DateTime");
        this.formatter = DateTimeFormat.forPattern((String)"yyyyMMdd HH:mm:ss");
    }

    @Override
    public String printValue(String symbol, VersatileData data, int decimals) {
        return this.formatter.print(data.time);
    }

    @Override
    public AbstractItem clone() {
        return new DateTime();
    }

    @Override
    public void setFormat(String format) throws Exception {
        try {
            this.formatter = DateTimeFormat.forPattern((String)format);
        }
        catch (Exception e) {
            throw new Exception(String.format(L.t((String)"Invalid DateTime format '%s'", (Object[])new Object[0]), format));
        }
    }
}

