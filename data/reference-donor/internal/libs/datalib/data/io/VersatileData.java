/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.io;

public class VersatileData {
    public static final int UNKNOWN_DATA = 0;
    public static final int TICK_DATA = 1;
    public static final int MINUTE_DATA = 2;
    public static final int DT_VOLUME = 1;
    public static final int DT_ASK = 2;
    public static final int DT_BID = 3;
    public static final int DT_OPEN = 4;
    public static final int DT_HIGH = 5;
    public static final int DT_LOW = 6;
    public static final int DT_CLOSE = 7;
    public static final int DT_INDICATOR_VALUE = 8;
    public static final int DT_TIME = 9;
    public static final int DT_UNUSED = 10;
    public static final int DT_CUSTOM_VALUE = 9999;
    public static final int ASK = 0;
    public static final int BID = 1;
    public static final long TimeNotDefined = Long.MIN_VALUE;
    public long time = Long.MIN_VALUE;
    public double ask;
    public double bid;
    public double open;
    public double high;
    public double low;
    public double close;
    public double volume;
    public double spread = 0.0;
    public int type;
    public int symbolHash;
    public int connectionHash;
    public long sessionStartTime;

    public void reset() {
        this.time = 0L;
        this.ask = 0.0;
        this.bid = 0.0;
        this.open = 0.0;
        this.high = 0.0;
        this.low = 0.0;
        this.close = 0.0;
        this.volume = 0.0;
        this.spread = 0.0;
    }

    public void set(int n, long l, int n2, int n3, double d, double d2, double d3, double d4, double d5) {
        this.type = n;
        this.time = l;
        this.connectionHash = n2;
        this.symbolHash = n3;
        this.open = d;
        this.high = d2;
        this.low = d3;
        this.close = d4;
        this.volume = d5;
    }

    public void set(int n, long l, int n2, int n3, double d, double d2, double d3) {
        this.type = n;
        this.time = l;
        this.connectionHash = n2;
        this.symbolHash = n3;
        this.ask = d;
        this.bid = d2;
        this.volume = d3;
    }

    public void copyFrom(VersatileData versatileData) {
        this.time = versatileData.time;
        this.ask = versatileData.ask;
        this.bid = versatileData.bid;
        this.open = versatileData.open;
        this.high = versatileData.high;
        this.low = versatileData.low;
        this.close = versatileData.close;
        this.volume = versatileData.volume;
        this.type = versatileData.type;
        this.symbolHash = versatileData.symbolHash;
        this.connectionHash = versatileData.connectionHash;
        this.sessionStartTime = versatileData.sessionStartTime;
    }

    public int getCheckSum() {
        return (int)((double)this.time + this.ask + this.bid + this.open + this.high + this.low + this.close + this.volume + (double)this.symbolHash + (double)this.connectionHash);
    }

    public String print() {
        return "type: " + this.type + ", time: " + this.time + ", ask: " + this.ask + ", bid: " + this.bid + ", open: " + this.open + ", high: " + this.high + ", low: " + this.low + ", close: " + this.close + ", volume: " + this.volume + ", symbolHash: " + this.symbolHash + ", connectionHash: " + this.connectionHash;
    }
}

