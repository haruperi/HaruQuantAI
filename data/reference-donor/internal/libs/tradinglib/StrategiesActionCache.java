/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategiesActionCache {
    private static final Logger Log = LoggerFactory.getLogger(StrategiesActionCache.class);
    private static final String lockName = "StrategiesActionCache";
    private static ArrayList<ResultsGroup> strategies = new ArrayList();

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void cutFrom(Databank databank, String[] stringArray) throws Exception {
        boolean bl = false;
        strategies.clear();
        for (int i = 0; i < stringArray.length; ++i) {
            String string = stringArray[i];
            ResultsGroup resultsGroup = null;
            try {
                resultsGroup = databank.getLocked(string, lockName);
                if (resultsGroup.specialValues().containsKey(SpecialValues.IsMergedPortfolio) && resultsGroup.getMergedResults() == null) {
                    resultsGroup.setMergedResults(StrategyMerger.getSplitResults(resultsGroup));
                }
                strategies.add(resultsGroup.clone());
                try {
                    databank.removeNoLock(string, true, false, false, lockName);
                }
                catch (Exception exception) {
                    Log.error("Cannot remove cut strategy '" + string + "'", (Throwable)exception);
                }
                continue;
            }
            catch (Exception exception) {
                bl = true;
                Log.error("Cannot cut strategy '" + string + "'", (Throwable)exception);
                continue;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(lockName);
                }
            }
        }
        databank.notifyListeners("removed");
        databank.updateBestResults();
        databank.refreshGrid();
        if (bl) {
            throw new Exception("Some of the strategies were not copied. Check log file for further details");
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void copyFrom(Databank databank, String[] stringArray) throws Exception {
        boolean bl = false;
        strategies.clear();
        for (int i = 0; i < stringArray.length; ++i) {
            String string = stringArray[i];
            ResultsGroup resultsGroup = null;
            try {
                resultsGroup = databank.getLocked(string, lockName);
                if (resultsGroup.specialValues().containsKey(SpecialValues.IsMergedPortfolio) && resultsGroup.getMergedResults() == null) {
                    resultsGroup.setMergedResults(StrategyMerger.getSplitResults(resultsGroup));
                }
                strategies.add(resultsGroup.clone());
                continue;
            }
            catch (Exception exception) {
                bl = true;
                Log.error("Cannot cut strategy '" + string + "'", (Throwable)exception);
                continue;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(lockName);
                }
            }
        }
        if (bl) {
            throw new Exception("Some of the strategies were not copied. Check log file for further details");
        }
    }

    public static void pasteTo(Databank databank) throws Exception {
        if (strategies.size() == 0) {
            throw new Exception("Nothing to paste");
        }
        for (int i = 0; i < strategies.size(); ++i) {
            databank.add(strategies.get(i).clone(), false);
        }
        databank.updateBestResults();
        databank.refreshGrid();
    }
}

