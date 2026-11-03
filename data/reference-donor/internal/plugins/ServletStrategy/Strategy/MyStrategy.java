/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.tradinglib.ChartData
 *  com.strategyquant.tradinglib.Parameter
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.engine.TradingSetup
 */
package com.strategyquant.plugin.Servlet.impl.Strategy;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.engine.TradingSetup;

public class MyStrategy
extends StrategyBase {
    @Parameter
    public int Period;
    private int count = 0;

    public void Initialize() throws Exception {
    }

    public void OnBarUpdate() throws Exception {
        ++this.count;
        this.Log.info("BAR UPDATE " + this.count);
    }

    public void callOnInit(TradingSetup tradingSetup) throws Exception {
    }

    public double getATRValue(ChartData chartData, int atrPeriod, int shift) throws TradingException {
        return 0.0;
    }
}

