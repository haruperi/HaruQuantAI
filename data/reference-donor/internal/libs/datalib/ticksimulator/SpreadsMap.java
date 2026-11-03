/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 */
package com.strategyquant.datalib.ticksimulator;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.InstrumentInfo;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import java.util.ArrayList;

public class SpreadsMap {
    Int2DoubleOpenHashMap map = new Int2DoubleOpenHashMap();
    private int lastUsedSpreadHashKey = 0;
    private double lastUsedSpread;

    public SpreadsMap(ArrayList<ChartDef> arrayList) {
        for (ChartDef chartDef : arrayList) {
            int n = chartDef.getConnectionHash() + chartDef.getSymbolHash();
            double d = chartDef.getSpread();
            InstrumentInfo instrumentInfo = chartDef.getInstrumentInfo();
            double d2 = d == -1.0 ? -1.0 : d * instrumentInfo.tickSize;
            this.map.put(n, d2);
        }
    }

    public double getSpread(int n) {
        if (this.lastUsedSpreadHashKey == n) {
            return this.lastUsedSpread;
        }
        this.lastUsedSpread = this.map.get(n);
        this.lastUsedSpreadHashKey = n;
        return this.lastUsedSpread;
    }

    public boolean containsKey(int n) {
        return this.map.containsKey(n);
    }
}

