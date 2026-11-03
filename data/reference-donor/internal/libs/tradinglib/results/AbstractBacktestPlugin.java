/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.tradinglib.backtest.IBacktester;
import com.strategyquant.tradinglib.results.IBacktestPlugin;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;

public abstract class AbstractBacktestPlugin
implements IBacktestPlugin {
    protected IBacktester backtester;
    protected IResultsGroupProvider rgProvider;

    @Override
    public void setBacktester(IBacktester iBacktester) {
        this.backtester = iBacktester;
    }

    @Override
    public void setResultsGroupProvider(IResultsGroupProvider iResultsGroupProvider) {
        this.rgProvider = iResultsGroupProvider;
    }
}

