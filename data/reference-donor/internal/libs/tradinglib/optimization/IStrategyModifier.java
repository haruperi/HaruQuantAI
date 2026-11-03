/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.indicator.IndicatorsObj;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.StrategyParamData;
import java.io.Serializable;
import org.jdom2.Element;

public interface IStrategyModifier
extends Serializable {
    public StrategyParamData createStrategyVariation(StrategyBase var1, OptimizationSettings var2, short[] var3) throws Exception;

    public StrategyBase createStrategyFromXml(Element var1, String var2) throws Exception;

    public IndicatorsObj createIndicatorsObject(StrategyBase var1);
}

