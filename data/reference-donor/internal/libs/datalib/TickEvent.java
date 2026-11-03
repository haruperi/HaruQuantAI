/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib;

public class TickEvent {
    private boolean isSet = false;
    private int symbolHash;
    private int connectionHash;
    private long time = -1L;
    private double ask;
    private double bid;
    private double volume;
    private long sessionStartTime;
    private long sessionEndTime;
    private boolean barOpen = false;
    private boolean barClose = false;

    public boolean isSet() {
        return this.isSet;
    }

    public void setIsSet(boolean bl) {
        this.isSet = bl;
    }

    public final int getSymbolHash() {
        return this.symbolHash;
    }

    public void setSymbolHash(int n) {
        this.symbolHash = n;
    }

    public long getSessionStartTime() {
        return this.sessionStartTime;
    }

    public void setSessionStartTime(long l) {
        this.sessionStartTime = l;
    }

    public long getSessionEndTime() {
        return this.sessionEndTime;
    }

    public void setSessionEndTime(long l) {
        this.sessionEndTime = l;
    }

    public final int getConnectionHash() {
        return this.connectionHash;
    }

    public void setConnectionHash(int n) {
        this.connectionHash = n;
    }

    public double getAsk() {
        return this.ask;
    }

    public void setAsk(double d) {
        this.ask = d;
    }

    public double getBid() {
        return this.bid;
    }

    public void setBid(double d) {
        this.bid = d;
    }

    public double getVolume() {
        return this.volume;
    }

    public void copyValues(TickEvent tickEvent) {
        this.time = tickEvent.time;
        this.symbolHash = tickEvent.symbolHash;
        this.connectionHash = tickEvent.connectionHash;
        this.bid = tickEvent.bid;
        this.ask = tickEvent.ask;
        this.volume = tickEvent.volume;
        this.sessionStartTime = tickEvent.sessionStartTime;
        this.sessionEndTime = tickEvent.sessionEndTime;
        this.barClose = tickEvent.barClose;
        this.barClose = tickEvent.barClose;
    }

    public long getTime() {
        return this.time;
    }

    public void setTime(long l) {
        this.time = l;
    }

    public void setVolume(double d) {
        this.volume = d;
    }

    public void set(long l, int n, int n2, double d, double d2, double d3, long l2, long l3, boolean bl, boolean bl2) {
        this.time = l;
        this.symbolHash = n2;
        this.connectionHash = n;
        this.bid = d;
        this.ask = d2;
        this.volume = d3;
        this.sessionStartTime = l2;
        this.sessionEndTime = l3;
        this.barOpen = bl;
        this.barClose = bl2;
    }

    public void set(long l, int n, int n2, double d, double d2, double d3, long l2, boolean bl, boolean bl2) {
        this.time = l;
        this.symbolHash = n2;
        this.connectionHash = n;
        this.bid = d;
        this.ask = d2;
        this.volume = d3;
        this.sessionStartTime = l2;
        this.barOpen = bl;
        this.barClose = bl2;
    }

    public void set(TickEvent tickEvent) {
        this.set(tickEvent.time, tickEvent.connectionHash, tickEvent.symbolHash, tickEvent.bid, tickEvent.ask, tickEvent.volume, tickEvent.sessionStartTime, tickEvent.sessionEndTime, tickEvent.barOpen, tickEvent.barClose);
    }

    public boolean isBarOpen() {
        return this.barOpen;
    }

    public boolean isBarClose() {
        return this.barClose;
    }

    public String toString() {
        StringBuffer stringBuffer = new StringBuffer();
        stringBuffer.append(this.ask);
        stringBuffer.append(",");
        stringBuffer.append(this.bid);
        return stringBuffer.toString();
    }
}

