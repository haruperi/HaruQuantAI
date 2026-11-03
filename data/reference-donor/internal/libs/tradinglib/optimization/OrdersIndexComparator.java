/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.ResultsGroup;
import java.util.Comparator;

public class OrdersIndexComparator
implements Comparator<ResultsGroup> {
    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        double d;
        double d2 = resultsGroup.specialValues().getDouble("OptIndexFitness", 0.0);
        if (d2 < (d = resultsGroup2.specialValues().getDouble("OptIndexFitness", 0.0))) {
            return -1;
        }
        if (d2 > d) {
            return 1;
        }
        return 0;
    }
}

