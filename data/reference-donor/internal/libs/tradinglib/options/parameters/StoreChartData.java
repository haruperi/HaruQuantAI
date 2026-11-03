/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;

public class StoreChartData
extends TradingOption {
    @Parameter(name="Store Chart Data", defaultValue="false", category="Build options")
    @Help(value="Store chart data in the backtest result?")
    public boolean StoreChartData;

    public StoreChartData() {
        this.inbuild = true;
    }

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) {
        return true;
    }

    public TradingOption clone() {
        StoreChartData storeChartData = new StoreChartData();
        storeChartData.StoreChartData = this.StoreChartData;
        return storeChartData;
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }
}

