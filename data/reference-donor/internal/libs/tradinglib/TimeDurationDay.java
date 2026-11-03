/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.TimeDuration;

public class TimeDurationDay
extends TimeDuration {
    public TimeDurationDay(int n) {
        super(n);
    }

    @Override
    public String toString() {
        return this.value + " " + L.t((String)"days", (Object[])new Object[0]);
    }

    @Override
    public int toSeconds(int n) {
        return n * 3600 * 24;
    }
}

