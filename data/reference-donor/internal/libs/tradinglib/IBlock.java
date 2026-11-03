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

public interface IBlock {
    public static final double True = 1.0;
    public static final double False = 0.0;

    public double evaluateBlock() throws TradingException;

    public double evaluateBlock(int var1) throws TradingException;

    public IBlock newInstance(StrategyBase var1, Element var2) throws BlockDefinitionException;

    public StrategyBase getStrategy();

    public IBlock clone(boolean var1, StrategyBase var2) throws BlockDefinitionException;

    public void setCustomData(String var1, int var2);

    public int getCustomData(String var1);

    public void copyCustomData(IBlock var1);

    public int getReturnType();

    public void setReturnType(int var1);

    public Element getCustomBlockXml(int var1) throws BlockDefinitionException;
}

