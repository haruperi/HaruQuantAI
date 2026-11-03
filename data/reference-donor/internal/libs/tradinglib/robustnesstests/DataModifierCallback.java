/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.io.VersatileData
 */
package com.strategyquant.tradinglib.robustnesstests;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;

public interface DataModifierCallback {
    public void modifyData(TickEvent var1);

    public void modifyData(TickEvent var1, double var2);

    public void modifyOHLCData(VersatileData var1);
}

