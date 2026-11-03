/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.conditions.DismissStruct
 *  com.strategyquant.tradinglib.correlation.CorrelationComputer
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.DismissStruct;
import com.strategyquant.tradinglib.correlation.CorrelationComputer;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioChecker {
    public static final Logger Log = LoggerFactory.getLogger((String)"PortfolioChecker");
    public static final String RESULT_OK = "OK";
    public static final String RESULT_INDEX = "result_index";
    private int correlationPeriod;
    private CorrelationType correlationType;
    private double maxCorrelation;
    private boolean allowNegativeCorrelation;
    private boolean addEmptyPeriods;
    private int maxFromSector;
    private PortfolioMasterSettings settings;
    private CorrelationComputer correlationComputer = new CorrelationComputer();
    private HashMap<String, Double> correlationsMap = new HashMap();
    private List<ResultsGroup> results = null;

    public PortfolioChecker(int correlationPeriod, CorrelationType correlationType, double maxCorrelation, boolean allowNegativeCorrelation, boolean addEmptyPeriods, int maxFromSector, PortfolioMasterSettings settings) {
        this.correlationPeriod = correlationPeriod;
        this.correlationType = correlationType;
        this.maxCorrelation = maxCorrelation;
        this.allowNegativeCorrelation = allowNegativeCorrelation;
        this.addEmptyPeriods = addEmptyPeriods;
        this.maxFromSector = maxFromSector;
        this.settings = settings;
    }

    public synchronized void setResults(List<ResultsGroup> results) {
        this.results = results;
    }

    public synchronized DismissStruct checkCorrectness(int[] combination, String portfolioName) {
        ArrayList<ResultsGroup> strategyResultsList = new ArrayList<ResultsGroup>();
        for (int index : combination) {
            strategyResultsList.add(this.results.get(index));
        }
        if (!this.checkMaxFromSector(strategyResultsList)) {
            return new DismissStruct(10016, L.t((String)"%s - dismissed, reason: %s", (Object[])new Object[]{portfolioName, L.t((String)"More strategies from the same sector than allowed.", (Object[])new Object[0])}));
        }
        String dismissMessage = this.checkCorrelation(strategyResultsList);
        if (dismissMessage != null) {
            return new DismissStruct(10015, L.t((String)"%s - dismissed, reason: %s", (Object[])new Object[]{portfolioName, dismissMessage}));
        }
        return null;
    }

    private synchronized boolean checkMaxFromSector(List<ResultsGroup> strategyResultsList) {
        if (this.maxFromSector == 0) {
            return true;
        }
        HashMap<String, Integer> countMap = new HashMap<String, Integer>();
        for (ResultsGroup result : strategyResultsList) {
            String sector = result.specialValues().getString(SpecialValues.Sector);
            if (sector == null) continue;
            if (countMap.containsKey(sector)) {
                int currentCount = (Integer)countMap.get(sector) + 1;
                if (currentCount > this.maxFromSector) {
                    return false;
                }
                countMap.put(sector, currentCount);
                continue;
            }
            countMap.put(sector, 1);
        }
        return true;
    }

    private synchronized String checkCorrelation(List<ResultsGroup> strategyResultsList) {
        if (this.maxCorrelation <= 0.0) {
            return null;
        }
        for (ResultsGroup result1 : strategyResultsList) {
            for (ResultsGroup result2 : strategyResultsList) {
                double corr;
                if (result1.equals(result2) || (corr = this.computeCorrelation(result1, result2)) == -99.0) continue;
                String combination = this.printCombination(result1, result2);
                if (!(corr > this.maxCorrelation) && (this.allowNegativeCorrelation || !(corr < 0.0))) continue;
                if (corr < 0.0) {
                    return L.t((String)"%s correlation %.2f < 0, negative correlation not allowed", (Object[])new Object[]{combination, corr});
                }
                return L.t((String)"%s correlation %.2f > %.2f", (Object[])new Object[]{combination, corr, this.maxCorrelation});
            }
        }
        return null;
    }

    private synchronized double computeCorrelation(ResultsGroup result1, ResultsGroup result2) {
        try {
            double corr;
            String key = this.key(result1, result2);
            if (this.correlationsMap.containsKey(key)) {
                corr = this.correlationsMap.get(key);
            } else {
                corr = this.correlationComputer.computeCorrelation(result1, result2, this.settings.correlationSampleType, this.correlationPeriod, this.correlationType, this.addEmptyPeriods);
                this.correlationsMap.put(key, corr);
            }
            return corr;
        }
        catch (Exception e) {
            Log.error("Failed to calculate correlation - " + e.getMessage(), (Throwable)e);
            return -99.0;
        }
    }

    private synchronized String key(ResultsGroup result1, ResultsGroup result2) {
        int index2;
        int index1 = result1.specialValues().getInt(RESULT_INDEX);
        return index1 > (index2 = result2.specialValues().getInt(RESULT_INDEX)) ? index1 + "," + index2 : index2 + "," + index1;
    }

    private synchronized String printCombination(ResultsGroup result1, ResultsGroup result2) {
        return result1.getName() + " - " + result2.getName();
    }
}

