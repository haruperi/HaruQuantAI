/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.broker;

public class BrokerDto {
    private String name;
    private String desc;
    private int customizedStocks;
    private int customizedInstruments;
    private int customizedSessions;
    private Integer id;
    private boolean system;
    private boolean mtUse;
    private String mtTimezone;
    private String postfix;
    private boolean stockPickerUse;

    public int getCustomizedStocks() {
        return this.customizedStocks;
    }

    public void setCustomizedStocks(int n) {
        this.customizedStocks = n;
    }

    public int getCustomizedInstruments() {
        return this.customizedInstruments;
    }

    public void setCustomizedInstruments(int n) {
        this.customizedInstruments = n;
    }

    public boolean isMtUse() {
        return this.mtUse;
    }

    public void setMtUse(boolean bl) {
        this.mtUse = bl;
    }

    public String getMtTimezone() {
        return this.mtTimezone;
    }

    public void setMtTimezone(String string) {
        this.mtTimezone = string;
    }

    public String getPostfix() {
        return this.postfix;
    }

    public void setPostfix(String string) {
        this.postfix = string;
    }

    public boolean isStockPickerUse() {
        return this.stockPickerUse;
    }

    public void setStockPickerUse(boolean bl) {
        this.stockPickerUse = bl;
    }

    public String getName() {
        return this.name;
    }

    public void setName(String string) {
        this.name = string;
    }

    public String getDesc() {
        return this.desc;
    }

    public void setDesc(String string) {
        this.desc = string;
    }

    public Integer getId() {
        return this.id;
    }

    public void setId(Integer n) {
        this.id = n;
    }

    public boolean isSystem() {
        return this.system;
    }

    public void setSystem(boolean bl) {
        this.system = bl;
    }

    public int getCustomizedSessions() {
        return this.customizedSessions;
    }

    public void setCustomizedSessions(int n) {
        this.customizedSessions = n;
    }
}

