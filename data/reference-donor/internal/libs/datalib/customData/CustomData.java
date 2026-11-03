/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.customData;

import com.strategyquant.lib.SQTime;
import java.util.Arrays;

public class CustomData {
    public long time = -1L;
    public double[] values = null;

    public CustomData(int n) {
        this.values = new double[n];
    }

    public void reset() {
        this.time = -1L;
        for (int i = 0; i < this.values.length; ++i) {
            this.values[i] = 0.0;
        }
    }

    public String toString() {
        if (this.time == -1L || this.values == null) {
            return null;
        }
        return SQTime.toDateMinuteString((long)this.time) + " - " + Arrays.toString(this.values);
    }
}

