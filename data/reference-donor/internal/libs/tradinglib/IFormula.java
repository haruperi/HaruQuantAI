/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.StrategyBase;
import org.jdom2.Element;

public interface IFormula {
    public double evaluateFormula(StrategyBase var1, String var2, double var3, int var5) throws TradingException;

    public IFormula newFormulaInstance(StrategyBase var1, Element var2) throws BlockDefinitionException;

    public boolean isNoneValue();

    public boolean isBooleanValue();
}

