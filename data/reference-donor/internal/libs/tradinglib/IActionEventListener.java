/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.StrategyBase;

public interface IActionEventListener {
    public void OnActionEvent(StrategyBase var1) throws TradingException;
}

