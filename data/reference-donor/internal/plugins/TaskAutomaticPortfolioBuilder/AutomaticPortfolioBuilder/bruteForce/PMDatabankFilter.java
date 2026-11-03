/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DefaultDatabankFilter
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DefaultDatabankFilter;

public class PMDatabankFilter
extends DefaultDatabankFilter {
    private byte sampleType;

    public PMDatabankFilter(int maxStrategies, boolean dismissTooSimilarStrategies, byte sampleType) {
        super(maxStrategies, dismissTooSimilarStrategies);
        this.sampleType = sampleType;
    }

    public double getRankValue(ResultsGroup rg) {
        try {
            return rg.getFitness(this.sampleType);
        }
        catch (Exception e) {
            Log.error("Cannot calculate rank value of strategy '" + rg.getName() + "'", (Throwable)e);
            return 0.0;
        }
    }
}

