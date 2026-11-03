/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.strategy.StrategyMerger
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import java.util.ArrayList;

public class PMPortfolioComputer {
    public ResultsGroup createPortfolio(ArrayList<ResultsGroup> results, String portfolioName, PortfolioMasterSettings settings) throws Exception {
        MoneyManagementMethod mmMethod = null;
        if (settings.mmMethodOptional) {
            mmMethod = settings.mmMethod;
        }
        return StrategyMerger.createSimulatedResult(null, results, (String)portfolioName, (float)settings.initialCapital, (MoneyManagementMethod)mmMethod);
    }
}

