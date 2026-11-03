/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.ticksimulator;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.ticksimulator.SpreadsMap;

public interface ITickSimulator {
    public void init(VersatileData var1);

    public boolean getNextTick(TickEvent var1);

    public void setSymbolsSpread(SpreadsMap var1);
}

