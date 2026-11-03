/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.results.stats.StatsComputer;
import com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;

public class MCResultsComputer {
    protected static final StatsTypeCombination combination = new StatsTypeCombination(0, 10, 127);

    public static RobustnessResults computeResults(OrdersList ordersList, SettingsMap settingsMap, SymbolsMap symbolsMap, Result result) throws Exception {
        SQStats sQStats;
        RobustnessResults robustnessResults = new RobustnessResults();
        StatsComputer statsComputer = new StatsComputer();
        statsComputer.initializeWithOrders(ordersList);
        if (result != null) {
            sQStats = result.stats((byte)0, (byte)10, (byte)127);
            double d = sQStats.getDouble("TotalTradingDays");
            double d2 = sQStats.getDouble("TotalTradingMonths");
            double d3 = sQStats.getDouble("TotalTradingYears");
            settingsMap.set("TotalTradingDays", (Object)d);
            settingsMap.set("TotalTradingMonths", (Object)d2);
            settingsMap.set("TotalTradingYears", (Object)d3);
        }
        robustnessResults.setOrdersValues(MCResultsComputer.computeOrdersValues(statsComputer, settingsMap, symbolsMap));
        sQStats = statsComputer.computeStats(null, combination, settingsMap);
        robustnessResults.setOriginalStats(sQStats);
        return robustnessResults;
    }

    public static RobustnessOrdersValues computeOrdersValues(StatsComputer statsComputer, SettingsMap settingsMap, SymbolsMap symbolsMap) throws Exception {
        statsComputer.filterBy("Portfolio", (byte)0, (byte)127);
        statsComputer.sortAndComputeOrderValues(settingsMap, symbolsMap);
        OrdersList ordersList = statsComputer.getFilteredOrders();
        RobustnessOrdersValues robustnessOrdersValues = new RobustnessOrdersValues(ordersList.size());
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            robustnessOrdersValues.set(i, order.PL);
        }
        return robustnessOrdersValues;
    }
}

