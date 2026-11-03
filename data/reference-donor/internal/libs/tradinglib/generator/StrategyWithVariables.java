/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.engine.TradingSetup;
import org.jdom2.Element;

public class StrategyWithVariables
extends StrategyBase {
    public StrategyWithVariables(Element element) {
        this.variables = new Variables(element);
    }

    @Override
    public void callOnInit(TradingSetup tradingSetup) throws Exception {
    }

    @Override
    public void Initialize() throws Exception {
    }

    @Override
    public void OnBarUpdate() throws Exception {
    }

    @Override
    public double getATRValue(ChartData chartData, int n, int n2) throws TradingException {
        return 0.0;
    }
}

