/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.basket;

import com.strategyquant.lib.SQTime;

public class StockDto {
    private Integer id;
    private String ticker;
    private Long dateFrom = -1L;
    private Long dateTo = -1L;
    public static final long TimeNotDefined = -1L;

    public boolean isActive() {
        return this.dateTo == null || this.dateTo.equals(-1L);
    }

    public Integer getId() {
        return this.id;
    }

    public void setId(Integer n) {
        this.id = n;
    }

    public String getTicker() {
        return this.ticker;
    }

    public void setTicker(String string) {
        this.ticker = string;
    }

    public Long getDateFrom() {
        return this.dateFrom;
    }

    public void setDateFrom(Long l) {
        this.dateFrom = l;
    }

    public Long getDateTo() {
        return this.dateTo;
    }

    public void setDateTo(Long l) {
        this.dateTo = l;
    }

    public String toString() {
        return this.id + ";" + this.ticker + ";" + SQTime.toDateString((long)this.dateFrom) + ";" + (this.dateTo == -1L ? "" : SQTime.toDateString((long)this.dateTo));
    }
}

