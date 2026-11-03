/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.TimeDuration;

public class TimeDurationHour
extends TimeDuration {
    public TimeDurationHour(int n) {
        super(n);
    }

    @Override
    public String toString() {
        return this.value + " " + L.t((String)"hours", (Object[])new Object[0]);
    }

    @Override
    public int toSeconds(int n) {
        return n * 3600;
    }
}

