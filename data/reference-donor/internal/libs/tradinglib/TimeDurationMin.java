/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.TimeDuration;

public class TimeDurationMin
extends TimeDuration {
    public TimeDurationMin(int n) {
        super(n);
    }

    @Override
    public String toString() {
        return this.value + " " + L.t((String)"mins", (Object[])new Object[0]);
    }

    @Override
    public int toSeconds(int n) {
        return n * 60;
    }
}

