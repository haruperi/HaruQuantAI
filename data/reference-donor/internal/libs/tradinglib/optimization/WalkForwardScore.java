/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.WalkForwardResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForwardScore {
    private static final Logger Log = LoggerFactory.getLogger(WalkForwardScore.class);

    public static synchronized void compute(DatabankColumn databankColumn, ResultsGroup resultsGroup, SQStats sQStats, WalkForwardResult walkForwardResult) {
        double d = 0.0;
        try {
            double d2 = 0.0;
            double d3 = 0.0;
            SQStats sQStats2 = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127);
            d2 = databankColumn.getNumericValue(sQStats2);
            d3 = databankColumn.getNumericValue(walkForwardResult.stats);
            d = SQUtils.round((double)(d3 / (d2 / 100.0)), (int)2);
        }
        catch (Exception exception) {
            Log.error("Error while computing WalkForwardScore. Exc.", (Throwable)exception);
        }
        sQStats.set(databankColumn.getStatsValueName(), d);
    }
}

