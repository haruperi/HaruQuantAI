/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.exits;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import org.jdom2.Element;

public class FixedProfit
extends AbstractExitLevel {
    private int Type;
    private int FixedPips;
    private double AtrMultiplicator;
    private int AtrPeriod;

    public FixedProfit(Element element, int n) throws Exception {
        super(element, n);
        this.Type = XMLUtil.getItemIntParam((Element)element, (String)"Type", (int)1);
        this.FixedPips = XMLUtil.getItemIntParam((Element)element, (String)"FixedPips", (int)50);
        this.AtrMultiplicator = XMLUtil.getItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)1.2);
        this.AtrPeriod = XMLUtil.getItemIntParam((Element)element, (String)"AtrPeriod", (int)20);
    }

    @Override
    public Element getXML() {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "FixedProfit");
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)this.Type);
        XMLUtil.setItemIntParam((Element)element, (String)"FixedPips", (int)this.FixedPips);
        XMLUtil.setItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)this.AtrMultiplicator);
        XMLUtil.setItemIntParam((Element)element, (String)"AtrPeriod", (int)this.AtrPeriod);
        return element;
    }

    @Override
    public void setForOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, double d2) throws TradingException {
        if (iLiveOrder.isFilled()) {
            this.setStrategy(strategyBase);
            this.setOrderPTValue(iLiveOrder, strategyBase);
        }
    }

    @Override
    public double getNettingPrice(StrategyBase strategyBase, ILiveOrder iLiveOrder, double d, double d2) throws TradingException {
        if (d2 == 0.0) {
            return 0.0;
        }
        int n = iLiveOrder.isLong() ? 1 : -1;
        double d3 = iLiveOrder.isNettingMode() && iLiveOrder.getLastOpenPrice() > 0.0 ? iLiveOrder.getLastOpenPrice() : iLiveOrder.getOpenPrice();
        double d4 = this.getByType(iLiveOrder, strategyBase);
        if (n > 0) {
            return d3 + d4;
        }
        return d3 - d4;
    }

    private void setOrderPTValue(ILiveOrder iLiveOrder, StrategyBase strategyBase) throws TradingException {
        int n = iLiveOrder.isLong() ? 1 : -1;
        double d = iLiveOrder.isNettingMode() && iLiveOrder.getLastOpenPrice() > 0.0 ? iLiveOrder.getLastOpenPrice() : iLiveOrder.getOpenPrice();
        double d2 = this.getByType(iLiveOrder, strategyBase);
        double d3 = n > 0 ? d + d2 : d - d2;
        this.setNewPT(iLiveOrder, d3, d);
    }

    private double getByType(ILiveOrder iLiveOrder, StrategyBase strategyBase) throws TradingException {
        if (this.Type == 1) {
            return strategyBase.convertPipsToRealPrice(iLiveOrder.getSymbol(), this.FixedPips);
        }
        ChartData chartData = strategyBase.MarketData.Chart(iLiveOrder.getSymbol());
        double d = strategyBase.getATRValue(chartData, this.AtrPeriod, 1);
        return this.AtrMultiplicator * SQUtils.round((double)d, (int)6);
    }

    public String toString() {
        if (this.Type == 1) {
            return String.format("at %d pips above Order Open price", this.FixedPips);
        }
        return String.format("at fixed profit %s * ATR(%d)", this.AtrMultiplicator, this.AtrPeriod);
    }

    public static Element generate(IRandomGenerator iRandomGenerator, ATMGenerateConfig aTMGenerateConfig) {
        int n;
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "FixedProfit");
        element.setAttribute("use", "true");
        int n2 = 50;
        double d = 1.2;
        int n3 = 20;
        if (iRandomGenerator.nextBool()) {
            n = 1;
            n2 = iRandomGenerator.nextInt(aTMGenerateConfig.fixedProfitFixedPipsMin, aTMGenerateConfig.fixedProfitFixedPipsMax, 1);
        } else {
            n = 2;
            d = iRandomGenerator.nextDouble(aTMGenerateConfig.fixedProfitATRMutliplierMin, aTMGenerateConfig.fixedProfitATRMutliplierMax, 0.05, 2);
            n3 = iRandomGenerator.nextInt(aTMGenerateConfig.fixedProfitATRPeriodMin, aTMGenerateConfig.fixedProfitATRPeriodMax, 1);
        }
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)n);
        XMLUtil.setItemIntParam((Element)element, (String)"FixedPips", (int)n2);
        XMLUtil.setItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)d);
        XMLUtil.setItemIntParam((Element)element, (String)"AtrPeriod", (int)n3);
        return element;
    }
}

