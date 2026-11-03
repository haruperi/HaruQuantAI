/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.formulas;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.StrategyBase;
import org.jdom2.Element;

public class EmptyFormula
implements IFormula {
    @Override
    public double evaluateFormula(StrategyBase strategyBase, String string, double d, int n) throws TradingException {
        return -9.9999999E7;
    }

    @Override
    public IFormula newFormulaInstance(StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        return null;
    }

    @Override
    public boolean isNoneValue() {
        return true;
    }

    @Override
    public boolean isBooleanValue() {
        return false;
    }
}

