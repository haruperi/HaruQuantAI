/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data;

import com.strategyquant.datalib.TickEvent;

public interface IDataBuffer {
    public void put(TickEvent var1);

    public void printRing();

    public long get(long var1, TickEvent[] var3);

    public long getOne(long var1, TickEvent var3);
}

