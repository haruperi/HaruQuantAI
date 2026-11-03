/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.SQUtils
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.DataManager.impl.Data.csvexport.items;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQUtils;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;

public abstract class AbstractItem {
    public static final String FormatSeparator = ":";
    public String name = null;
    public String key = null;
    public String format = null;
    public String header = null;
    public String value = null;
    public DateTimeFormatter formatter;
    public int count = 1;

    public AbstractItem(String name, String key, String header) {
        this.name = name;
        this.key = key;
        this.header = header;
    }

    public JSONObject toJson() {
        return new JSONObject().put("name", (Object)this.name).put("key", (Object)this.key).put("format", (Object)this.format).put("header", (Object)this.header);
    }

    public static String format(String key, String format) {
        return key + FormatSeparator + format;
    }

    public abstract String printValue(String var1, VersatileData var2, int var3);

    protected String d(double value, int decimals) {
        return SQUtils.d2String((double)value, (int)decimals);
    }

    public abstract AbstractItem clone();

    public void setFormat(String format) throws Exception {
        this.format = format;
    }
}

