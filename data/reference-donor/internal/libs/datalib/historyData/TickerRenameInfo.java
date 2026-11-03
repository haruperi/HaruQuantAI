/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.historyData;

import com.strategyquant.lib.SQTime;

public class TickerRenameInfo {
    private String tickerFrom;
    private String tickerTo;
    private Long date;

    public String getTickerFrom() {
        return this.tickerFrom;
    }

    public void setTickerFrom(String string) {
        this.tickerFrom = string;
    }

    public String getTickerTo() {
        return this.tickerTo;
    }

    public void setTickerTo(String string) {
        this.tickerTo = string;
    }

    public Long getDate() {
        return this.date;
    }

    public void setDate(Long l) {
        this.date = l;
    }

    public String toString() {
        return this.tickerFrom + " -> " + this.tickerTo + " at " + SQTime.toDateString((long)this.date);
    }
}

