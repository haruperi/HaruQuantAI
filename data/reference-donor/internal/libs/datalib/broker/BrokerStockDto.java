/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.broker;

public class BrokerStockDto {
    private Integer id;
    private String ticker;

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

    public String toString() {
        return this.id + ";" + this.ticker;
    }
}

