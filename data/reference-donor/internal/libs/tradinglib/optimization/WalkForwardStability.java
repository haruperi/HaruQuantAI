/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForwardStability {
    private static final Logger Log = LoggerFactory.getLogger(WalkForwardStability.class);

    public static synchronized void compute(DatabankColumn databankColumn, SQStats sQStats, WalkForwardResult walkForwardResult) {
        double d = 0.0;
        try {
            double d2;
            double d3;
            double d4 = 0.0;
            double d5 = 0.0;
            double d6 = 0.0;
            double d7 = 0.0;
            ArrayList<WalkForwardPeriod> arrayList = walkForwardResult.wfPeriods;
            for (int i = 0; i < arrayList.size() - 1; ++i) {
                WalkForwardPeriod walkForwardPeriod = arrayList.get(i);
                d4 += walkForwardPeriod.optimizationStatData == null ? 0.0 : databankColumn.getNumericValue(walkForwardPeriod.optimizationStatData);
                d5 += walkForwardPeriod.runStatData == null ? 0.0 : databankColumn.getNumericValue(walkForwardPeriod.runStatData);
                d6 += (double)SQTime.getDaysBetween((long)walkForwardPeriod.optimizeFrom, (long)walkForwardPeriod.optimizeTo);
                d7 += (double)SQTime.getDaysBetween((long)walkForwardPeriod.runFrom, (long)walkForwardPeriod.runTo);
            }
            if (databankColumn.isDependentOnTradingPeriod()) {
                d3 = SQUtils.safeDivide((double)d4, (double)d6);
                d2 = SQUtils.safeDivide((double)d5, (double)d7);
            } else {
                d3 = d4;
                d2 = d5;
            }
            double d8 = SQUtils.safeDivide((double)d2, (double)d3) * 100.0;
            d = SQUtils.round((double)d8, (int)2);
        }
        catch (Exception exception) {
            Log.error("Error while computing WalkForward Stability. Exc.", (Throwable)exception);
        }
        sQStats.set(databankColumn.getStatsValueName(), d);
    }
}

