/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.TimeDuration;

public class TimeDurationOther
extends TimeDuration {
    public TimeDurationOther() {
        super(0);
    }

    @Override
    public String toString() {
        return L.t((String)"Others", (Object[])new Object[0]);
    }

    @Override
    public int toSeconds(int n) {
        return Integer.MAX_VALUE;
    }
}

