/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TimePeriod
 *  com.strategyquant.lib.TimePeriods
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.longs.Long2ObjectMap$Entry
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.correlation;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.lib.TimePeriods;
import com.strategyquant.tradinglib.CorrelationLib;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.correlation.CorrelationPeriods;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CorrelationComputer {
    public static final Logger Log = LoggerFactory.getLogger((String)"CorrelationComputer");
    public static final int ERROR_VALUE = -99;
    public TimePeriod range;
    public String[] periodsStr;
    public double[] values1;
    public double[] values2;

    public double computeCorrelation(ResultsGroup resultsGroup, ResultsGroup resultsGroup2, byte by, int n, CorrelationType correlationType, boolean bl) {
        try {
            OrdersList ordersList = by == 127 ? resultsGroup.orders() : resultsGroup.orders().filter("Portfolio", (byte)0, by);
            OrdersList ordersList2 = by == 127 ? resultsGroup2.orders() : resultsGroup2.orders().filter("Portfolio", (byte)0, by);
            CorrelationPeriods correlationPeriods = this.precomputePeriods(resultsGroup.getName(), resultsGroup2.getName(), ordersList, ordersList2, n, correlationType);
            double d = this.computeCorrelation(bl, resultsGroup.getName(), resultsGroup2.getName(), ordersList, ordersList2, correlationPeriods, correlationType);
            return SQUtils.round2((double)d);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return -99.0;
        }
    }

    public double computeCorrelation(boolean bl, String string, String string2, OrdersList ordersList, OrdersList ordersList2, CorrelationPeriods correlationPeriods, CorrelationType correlationType) {
        try {
            if (ordersList == null || ordersList2 == null || ordersList.size() == 0 || ordersList2.size() == 0) {
                return -99.0;
            }
            DoubleArrayList doubleArrayList = new DoubleArrayList();
            DoubleArrayList doubleArrayList2 = new DoubleArrayList();
            TimePeriods timePeriods = (TimePeriods)correlationPeriods.get(string);
            TimePeriods timePeriods2 = (TimePeriods)correlationPeriods.get(string2);
            for (Long2ObjectMap.Entry entry : timePeriods.long2ObjectEntrySet()) {
                TimePeriod timePeriod = (TimePeriod)timePeriods.get(entry.getLongKey());
                TimePeriod timePeriod2 = (TimePeriod)timePeriods2.get(entry.getLongKey());
                if (!bl && timePeriod.value == 0.0 && timePeriod2.value == 0.0 || correlationType.shouldSkipPeriod(timePeriod.value, timePeriod2.value)) continue;
                doubleArrayList.add(timePeriod.value);
                doubleArrayList2.add(timePeriod2.value);
            }
            this.values1 = doubleArrayList.toDoubleArray();
            this.values2 = doubleArrayList2.toDoubleArray();
            return CorrelationComputer.calculateCorrelation(this.values1, this.values2);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return -99.0;
        }
    }

    public static double calculateCorrelation(double[] dArray, double[] dArray2) {
        double d = 0.0;
        double d2 = 0.0;
        double d3 = 0.0;
        double d4 = 0.0;
        double d5 = 0.0;
        double d6 = 0.0;
        double d7 = 0.0;
        double d8 = 0.0;
        double d9 = 0.0;
        for (int i = 0; i < dArray.length; ++i) {
            double d10 = dArray[i];
            double d11 = dArray2[i];
            d += d10 * d11;
            d2 += d10;
            d3 += d10 * d10;
            d4 += d11;
            d5 += d11 * d11;
            d6 += 1.0;
        }
        if (d6 > 0.0) {
            d7 = d - d2 * d4 / d6;
            d8 = d3 - d2 * d2 / d6;
            d9 = d5 - d4 * d4 / d6;
        }
        if (dArray.length == 0 || d8 == 0.0 || d9 == 0.0 || d6 == 0.0) {
            return 1.0;
        }
        return d7 / Math.sqrt(d8 * d9);
    }

    public static double calculateSimilarity(double[] dArray, double[] dArray2) {
        double d = 0.0;
        double d2 = Double.MAX_VALUE;
        double d3 = -1.7976931348623157E308;
        for (int i = 0; i < dArray.length; ++i) {
            if (dArray[i] < d2) {
                d2 = dArray[i];
            }
            if (dArray2[i] < d2) {
                d2 = dArray2[i];
            }
            if (dArray[i] > d3) {
                d3 = dArray[i];
            }
            if (!(dArray2[i] > d3)) continue;
            d3 = dArray2[i];
        }
        double d4 = d3 - d2;
        for (int i = 0; i < dArray.length; ++i) {
            double d5 = Math.abs(dArray[i] - dArray2[i]);
            d += (d5 /= d4);
        }
        return 1.0 - d / (double)dArray.length;
    }

    public CorrelationPeriods precomputePeriods(String string, String string2, OrdersList ordersList, OrdersList ordersList2, int n, CorrelationType correlationType) throws Exception {
        CorrelationPeriods correlationPeriods = new CorrelationPeriods();
        TimePeriod timePeriod = CorrelationLib.getPeriod(ordersList);
        long l = timePeriod.from;
        long l2 = timePeriod.to;
        timePeriod = CorrelationLib.getPeriod(ordersList2);
        if (timePeriod.from < l) {
            l = timePeriod.from;
        }
        if (timePeriod.to > l2) {
            l2 = timePeriod.to;
        }
        TimePeriods timePeriods = CorrelationLib.generatePeriods(n, l, l2);
        TimePeriods timePeriods2 = timePeriods.clone();
        correlationType.computePeriods(ordersList, n, timePeriods);
        correlationPeriods.put(string, timePeriods);
        correlationType.computePeriods(ordersList2, n, timePeriods2);
        correlationPeriods.put(string2, timePeriods2);
        return correlationPeriods;
    }
}

