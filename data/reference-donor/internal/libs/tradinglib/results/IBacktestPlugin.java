/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.tradinglib.backtest.IBacktester;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.servlet.IServletPlugin;

public interface IBacktestPlugin
extends IServletPlugin {
    public void setBacktester(IBacktester var1);

    public void setResultsGroupProvider(IResultsGroupProvider var1);
}

