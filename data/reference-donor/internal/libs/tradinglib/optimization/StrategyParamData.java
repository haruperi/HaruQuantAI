/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.StrategyBase;

public class StrategyParamData {
    private StrategyBase strategy;
    private String strParams;

    public StrategyParamData(StrategyBase strategyBase, String string) {
        this.strategy = strategyBase;
        this.strParams = string;
    }

    public StrategyBase getStrategy() {
        return this.strategy;
    }

    public String getParams() {
        return this.strParams;
    }
}

