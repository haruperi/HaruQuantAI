/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtest;

public class BacktestDataFeedElement {
    static final byte TYPE_UNKNOWN = 0;
    static final byte TYPE_TICK = 1;
    static final byte TYPE_OHLC = 2;
    private byte type;
    private byte hashPairIndex;
    private long time;
    private double data1;
    private double data2;
    private double data3;
    private double[] dataX;
    private long sessionStartTime;

    public void setTickData(long l, byte by, double d, double d2, double d3, long l2) {
        this.type = 1;
        this.time = l;
        this.hashPairIndex = by;
        this.data1 = d;
        this.data2 = d2;
        this.data3 = d3;
        this.sessionStartTime = l2;
    }

    public void setOhlcData(long l, byte by, double d, double d2, double d3, double d4, double d5, long l2) {
        this.type = (byte)2;
        this.time = l;
        this.hashPairIndex = by;
        this.data1 = d;
        this.data2 = d2;
        this.data3 = d5;
        this.dataX = new double[2];
        this.dataX[0] = d3;
        this.dataX[1] = d4;
        this.sessionStartTime = l2;
    }

    public void reset() {
        this.type = 0;
        this.dataX = null;
    }

    public void setFromElement(BacktestDataFeedElement backtestDataFeedElement) {
        this.type = backtestDataFeedElement.type;
        this.time = backtestDataFeedElement.time;
        this.hashPairIndex = backtestDataFeedElement.hashPairIndex;
        if (this.type == 1) {
            this.data1 = backtestDataFeedElement.data1;
            this.data2 = backtestDataFeedElement.data2;
            this.data3 = backtestDataFeedElement.data3;
        } else {
            this.data1 = backtestDataFeedElement.data1;
            this.data2 = backtestDataFeedElement.data2;
            this.data3 = backtestDataFeedElement.data3;
            if (this.dataX == null) {
                this.dataX = new double[2];
            }
            for (int i = 0; i < 2; ++i) {
                this.dataX[i] = backtestDataFeedElement.dataX[i];
            }
        }
    }

    public byte getType() {
        return this.type;
    }

    public long getTime() {
        return this.time;
    }

    public byte getHashPairIndex() {
        return this.hashPairIndex;
    }

    public double getOpen() {
        return this.data1;
    }

    public double getHigh() {
        return this.data2;
    }

    public double getLow() {
        return this.dataX[0];
    }

    public double getClose() {
        return this.dataX[1];
    }

    public double getVolume() {
        return this.data3;
    }

    public double getBid() {
        return this.data1;
    }

    public double getAsk() {
        return this.data2;
    }

    public long getSessionStartTime() {
        return this.sessionStartTime;
    }
}

