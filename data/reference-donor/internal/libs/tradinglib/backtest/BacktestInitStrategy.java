/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.TradingSetup;

public class BacktestInitStrategy
extends StrategyBase {
    @Override
    public void callOnInit(TradingSetup tradingSetup) throws Exception {
        this.tradingSetup = tradingSetup;
        this.initializeFromMarketData(tradingSetup.getMarketData());
        this.dismissBadStrategies = tradingSetup.getDismissBadStrategies();
        this.warningsBadStrategies = tradingSetup.getWarningsBadStrategies();
        this.Initialize();
    }

    @Override
    public void Initialize() throws Exception {
    }

    @Override
    public void OnBarUpdate() throws Exception {
    }

    @Override
    public double getATRValue(ChartData chartData, int n, int n2) throws TradingException {
        return 0.0;
    }
}

