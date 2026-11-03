/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtest;

public class StartDataInfo {
    public long realDataStartTime;
    public int reservedBars;
    public long realDataEndTime;

    public void copyFrom(StartDataInfo startDataInfo) {
        this.realDataStartTime = startDataInfo.realDataStartTime;
        this.reservedBars = startDataInfo.reservedBars;
        this.realDataEndTime = startDataInfo.realDataEndTime;
    }
}

