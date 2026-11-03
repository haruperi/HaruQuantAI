/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.robustnesstests.SequentialOptimizationResults;

public interface ISequentialOptimizationCompleteListener {
    public void onFinish(boolean var1, StrategyBase var2, SequentialOptimizationResults var3, ResultsGroup var4);
}

