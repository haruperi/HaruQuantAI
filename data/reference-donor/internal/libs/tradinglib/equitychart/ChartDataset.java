/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.JsonCreator
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.equitychart.Zoom;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;

public abstract class ChartDataset {
    public static final String TYPE_LINE = "line";
    public static final String TYPE_BAR = "bar";
    public static final String TYPE_POINT = "point";
    public String key;
    public String name = "";
    public String type = "line";
    public String color = null;
    public String colorDark = null;
    public int thickness = 1;
    public long[] xVals;
    public double[] yVals;
    public int length = 0;
    public int index = -1;
    public int decimals = 2;
    private DateTimeFormatter dtf = DateTimeFormat.forPattern((String)"yyyy-MM-dd");

    public void d3Format() {
        this.decimals = 3;
    }

    public int getSize() {
        return this.xVals.length;
    }

    public ChartDataset(String string, int n) {
        this.key = string;
        this.length = n;
        this.xVals = new long[n];
        this.yVals = new double[n];
    }

    public void addValue(long l, double d) {
        ++this.index;
        this.xVals[this.index] = l;
        this.yVals[this.index] = d;
    }

    protected String formatTime(long l) {
        return SQTime.toString((long)l, (DateTimeFormatter)this.dtf);
    }

    public double d(double d) {
        return SQUtils.round((double)d, (int)this.decimals);
    }

    public abstract void fillJSON(JsonCreator var1, Zoom var2, boolean var3);

    public abstract JSONObject toJSON(Zoom var1, boolean var2);
}

