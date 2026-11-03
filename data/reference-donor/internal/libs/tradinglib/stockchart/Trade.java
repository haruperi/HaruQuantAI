/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.stockchart;

public class Trade {
    private boolean shortTrade;
    private long id;
    private long index;
    private long openTime;
    private long closeTime;
    private long realOpenTime;
    private long realCloseTime;
    private double openValue;
    private double closeValue;
    private double SLValue;
    private double PTValue;
    private long openId;
    private long closeId;

    public boolean isShortTrade() {
        return this.shortTrade;
    }

    public void setShortTrade(boolean bl) {
        this.shortTrade = bl;
    }

    public long getOpenTime() {
        return this.openTime;
    }

    public void setOpenTime(long l) {
        this.openTime = l;
    }

    public long getCloseTime() {
        return this.closeTime;
    }

    public void setCloseTime(long l) {
        this.closeTime = l;
    }

    public double getOpenValue() {
        return this.openValue;
    }

    public void setOpenValue(double d) {
        this.openValue = d;
    }

    public double getCloseValue() {
        return this.closeValue;
    }

    public void setCloseValue(double d) {
        this.closeValue = d;
    }

    public long getOpenId() {
        return this.openId;
    }

    public void setOpenId(long l) {
        this.openId = l;
    }

    public long getCloseId() {
        return this.closeId;
    }

    public void setCloseId(long l) {
        this.closeId = l;
    }

    public long getId() {
        return this.id;
    }

    public void setId(long l) {
        this.id = l;
    }

    public long getRealOpenTime() {
        return this.realOpenTime;
    }

    public void setRealOpenTime(long l) {
        this.realOpenTime = l;
    }

    public long getRealCloseTime() {
        return this.realCloseTime;
    }

    public void setRealCloseTime(long l) {
        this.realCloseTime = l;
    }

    public long getIndex() {
        return this.index;
    }

    public void setIndex(long l) {
        this.index = l;
    }

    public double getSLValue() {
        return this.SLValue;
    }

    public void setSLValue(double d) {
        this.SLValue = d;
    }

    public double getPTValue() {
        return this.PTValue;
    }

    public void setPTValue(double d) {
        this.PTValue = d;
    }
}

