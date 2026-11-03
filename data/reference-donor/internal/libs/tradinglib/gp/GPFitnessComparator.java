/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.gp.IGPNode;
import java.util.Comparator;

public class GPFitnessComparator<T extends IGPNode>
implements Comparator<T> {
    private boolean natural;
    private byte sampleType;

    public GPFitnessComparator(boolean bl, byte by) {
        this.natural = bl;
        this.sampleType = by;
    }

    @Override
    public int compare(T t, T t2) {
        if (t == null || t2 == null) {
            return 0;
        }
        if (this.natural) {
            return Double.compare(t2.getFitness(this.sampleType), t.getFitness(this.sampleType));
        }
        return -1 * Double.compare(t2.getFitness(this.sampleType), t.getFitness(this.sampleType));
    }
}

