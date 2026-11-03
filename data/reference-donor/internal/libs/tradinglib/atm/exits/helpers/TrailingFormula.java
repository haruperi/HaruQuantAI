/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQUtils
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.exits.helpers;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.BlockDefinitionException;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.StrategyBase;
import org.jdom2.Element;

public class TrailingFormula
implements IFormula {
    private int type;
    private int fixedPips = -99999999;
    private double atrMultiplicator = -9.9999999E7;
    private int atrPeriod;
    private int cachedBars = -1;
    private StrategyBase cachedStrategy = null;
    private double cachedATR;

    public TrailingFormula(int n, int n2, double d, int n3) {
        this.type = n;
        this.fixedPips = n2;
        this.atrMultiplicator = d;
        this.atrPeriod = n3;
    }

    @Override
    public double evaluateFormula(StrategyBase strategyBase, String string, double d, int n) throws TradingException {
        if (this.type == 1) {
            return this.evaluateFixedPips(strategyBase, string, d, n);
        }
        return this.evaluateATRBased(strategyBase, string, d, n);
    }

    private double evaluateATRBased(StrategyBase strategyBase, String string, double d, int n) throws TradingException {
        if (this.atrMultiplicator == -9.9999999E7) {
            return -9.9999999E7;
        }
        ChartData chartData = strategyBase.MarketData.Chart(string);
        double d2 = SQUtils.round((double)this.getCachedATR(chartData, strategyBase), (int)6);
        double d3 = this.atrMultiplicator * d2;
        if (n == 1) {
            return SQUtils.round((double)(d - d3), (int)5);
        }
        return SQUtils.round((double)(d + d3), (int)5);
    }

    private double getCachedATR(ChartData chartData, StrategyBase strategyBase) throws TradingException {
        int n = chartData.Bars();
        if (n != this.cachedBars || this.cachedStrategy != strategyBase) {
            this.cachedBars = n;
            this.cachedStrategy = strategyBase;
            this.cachedATR = SQUtils.round6((double)strategyBase.getATRValue(chartData, this.atrPeriod, 1));
        }
        return this.cachedATR;
    }

    private double evaluateFixedPips(StrategyBase strategyBase, String string, double d, int n) throws TradingException {
        if (this.fixedPips == -99999999) {
            return -9.9999999E7;
        }
        double d2 = strategyBase.convertPipsToRealPrice(string, this.fixedPips);
        if (n == 1) {
            return strategyBase.MarketData.Chart(string).Bid() - d2;
        }
        return strategyBase.MarketData.Chart(string).Ask() + d2;
    }

    @Override
    public IFormula newFormulaInstance(StrategyBase strategyBase, Element element) throws BlockDefinitionException {
        return null;
    }

    @Override
    public boolean isNoneValue() {
        return false;
    }

    @Override
    public boolean isBooleanValue() {
        return false;
    }
}

