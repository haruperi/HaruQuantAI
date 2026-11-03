/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.lib.SQTime;

public class BarData {
    public long time;
    public float open;
    public float high;
    public float low;
    public float close;
    public float volume;
    public double value;

    public String toString() {
        return String.format("%s - o=%s,h=%s,l=%s,c=%s", SQTime.toDateString((long)this.time), Float.valueOf(this.open), Float.valueOf(this.high), Float.valueOf(this.low), Float.valueOf(this.close));
    }
}

