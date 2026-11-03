/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.equitychart;

public class Zoom {
    public boolean active = false;
    public int width = 1024;
    public long minX;
    public long maxX;

    public void reset() {
        this.active = false;
        this.width = 1024;
    }

    public Long getMin(long[] lArray) {
        if (this.active) {
            return this.minX;
        }
        return lArray.length > 0 ? lArray[0] : 0L;
    }

    public Long getMax(long[] lArray) {
        if (this.active) {
            return this.maxX;
        }
        return lArray.length > 0 ? lArray[lArray.length - 1] : 0L;
    }
}

