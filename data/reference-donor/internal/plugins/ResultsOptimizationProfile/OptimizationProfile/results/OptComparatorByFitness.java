/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.results;

import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import java.util.Comparator;

public class OptComparatorByFitness
implements Comparator<OptimizationTestResult> {
    @Override
    public int compare(OptimizationTestResult c1, OptimizationTestResult c2) {
        if (c1.stats.getDouble("Fitness") < c2.stats.getDouble("Fitness")) {
            return 1;
        }
        if (c1.stats.getDouble("Fitness") > c2.stats.getDouble("Fitness")) {
            return -1;
        }
        return 0;
    }
}

