/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.options.parameters;

import com.strategyquant.tradinglib.ForEngine;
import com.strategyquant.tradinglib.Help;
import com.strategyquant.tradinglib.Parameter;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;

public class ReservedBars
extends TradingOption {
    @Parameter(name="Reserved bars", defaultValue="50", category="Reserved bars")
    @Help(value="Bars in the beginning held in reserve before starting trading. This number should be bigger than any period used in strategy and should be as same as in Tradestation/MultiCharts.")
    @ForEngine(value="MC,TS")
    public int ReservedBars;

    public ReservedBars() {
        this.inbuild = true;
    }

    @Override
    public boolean OnBarUpdate(StrategyBase strategyBase) {
        return true;
    }

    public TradingOption clone() {
        ReservedBars reservedBars = new ReservedBars();
        reservedBars.ReservedBars = this.ReservedBars;
        return reservedBars;
    }

    @Override
    public boolean isUsedInTrading() {
        return false;
    }
}

