/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;

public class LimitOver
extends TradingOption {
    @Parameter(name="Limit Over", defaultValue="0", category="Stockpicker", minValue=0.0, maxValue=100.0, step=0.01)
    @Help(value="Limit Order is filled only if the price exceeds the limit by at least X %.")
    @ForEngine(value="SP,SA")
    public double LimitOver;

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) throws Exception {
        return true;
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }

    @Override
    public TradingOption getClone() {
        LimitOver limitOver = new LimitOver();
        limitOver.LimitOver = this.LimitOver;
        return limitOver;
    }
}

