/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;

public class FuturesVersatileData
extends VersatileData {
    public double openInterest;

    @Override
    public void reset() {
        super.reset();
        this.openInterest = 0.0;
    }

    public void set(int n, long l, int n2, int n3, double d, double d2, double d3, double d4, double d5, double d6) {
        super.set(n, l, n2, n3, d, d2, d3, d4, d5);
        this.openInterest = d6;
    }

    public void copyFrom(FuturesVersatileData futuresVersatileData) {
        super.copyFrom(futuresVersatileData);
        this.openInterest = futuresVersatileData.openInterest;
    }

    @Override
    public int getCheckSum() {
        return super.getCheckSum() + (int)this.openInterest;
    }

    @Override
    public String print() {
        return "type: " + this.type + ", time: " + this.time + ", ask: " + this.ask + ", bid: " + this.bid + ", open: " + this.open + ", high: " + this.high + ", low: " + this.low + ", close: " + this.close + ", volume: " + this.volume + ", openInterest:" + this.openInterest + ", symbolHash: " + this.symbolHash + ", connectionHash: " + this.connectionHash;
    }

    public String toString() {
        return "FuturesVersatileData [time:" + SQTime.toDateMinuteString((long)this.time);
    }
}

