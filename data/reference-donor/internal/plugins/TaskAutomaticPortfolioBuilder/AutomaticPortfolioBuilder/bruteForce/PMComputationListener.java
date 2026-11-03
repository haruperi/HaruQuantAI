/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioCombination;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import java.util.ArrayList;

public interface PMComputationListener {
    public PortfolioCombination checkPortfolio(int[] var1) throws Exception;

    public ArrayList<ResultsGroup> getResults(int[] var1) throws Exception;

    public void portfolioComputed(BacktestResult var1) throws Exception;

    public void printLog(String var1);

    public void resetStats();

    public boolean isStopped();
}

