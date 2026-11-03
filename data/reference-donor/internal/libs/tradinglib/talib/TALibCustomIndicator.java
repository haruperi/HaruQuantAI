/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.debug.Debugger;

public abstract class TALibCustomIndicator
extends Debugger {
    protected SettingsMap params;
    protected StrategyBase Strategy;
    protected float[] o;
    protected float[] h;
    protected float[] l;
    protected float[] c;
    protected float[] v;
    protected float[] in0;
    protected float[] in1;

    public abstract float[][] calculate();

    protected void init(SettingsMap settingsMap, StrategyBase strategyBase, float[] fArray, float[] fArray2, float[] fArray3, float[] fArray4, float[] fArray5, float[] fArray6, float[] fArray7) {
        this.params = settingsMap;
        this.Strategy = strategyBase;
        this.o = fArray;
        this.h = fArray2;
        this.l = fArray3;
        this.c = fArray4;
        this.v = fArray5;
        this.in0 = fArray6;
        this.in1 = fArray7;
    }
}

