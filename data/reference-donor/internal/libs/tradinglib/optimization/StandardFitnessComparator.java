/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.ResultsGroup;
import java.util.Comparator;

public class StandardFitnessComparator
implements Comparator<ResultsGroup> {
    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        double d;
        double d2 = resultsGroup.getFitness((byte)10);
        if (d2 < (d = resultsGroup2.getFitness((byte)10))) {
            return 1;
        }
        if (d2 > d) {
            return -1;
        }
        return 0;
    }
}

