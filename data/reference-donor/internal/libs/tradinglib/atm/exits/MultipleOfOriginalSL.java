/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.exits;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import org.jdom2.Element;

public class MultipleOfOriginalSL
extends AbstractExitLevel {
    private double Multiplicator;

    public MultipleOfOriginalSL(Element element, int n) throws Exception {
        super(element, n);
        this.Multiplicator = XMLUtil.getItemDoubleParam((Element)element, (String)"Multiplicator", (double)0.01);
    }

    @Override
    public Element getXML() {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "MultipleOfOriginalSL");
        XMLUtil.setItemDoubleParam((Element)element, (String)"Multiplicator", (double)this.Multiplicator);
        return element;
    }

    @Override
    public void setForOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, double d2) throws TradingException {
        if (iLiveOrder.isFilled()) {
            this.setStrategy(strategyBase);
            this.setOrderPTValue(iLiveOrder, strategyBase, d);
        }
    }

    @Override
    public double getNettingPrice(StrategyBase strategyBase, ILiveOrder iLiveOrder, double d, double d2) {
        if (d == -9.9999999E7) {
            return -9.9999999E7;
        }
        int n = iLiveOrder.isLong() ? 1 : -1;
        double d3 = iLiveOrder.isNettingMode() && iLiveOrder.getLastOpenPrice() > 0.0 ? iLiveOrder.getLastOpenPrice() : iLiveOrder.getOpenPrice();
        double d4 = Math.abs(d3 - d);
        double d5 = this.Multiplicator * d4;
        return d3 + (double)n * d5;
    }

    private void setOrderPTValue(ILiveOrder iLiveOrder, StrategyBase strategyBase, double d) throws TradingException {
        if (d == -9.9999999E7) {
            return;
        }
        int n = iLiveOrder.isLong() ? 1 : -1;
        double d2 = iLiveOrder.isNettingMode() && iLiveOrder.getLastOpenPrice() > 0.0 ? iLiveOrder.getLastOpenPrice() : iLiveOrder.getOpenPrice();
        double d3 = Math.abs(d2 - d);
        double d4 = this.Multiplicator * d3;
        double d5 = d2 + (double)n * d4;
        this.setNewPT(iLiveOrder, d5, d2);
    }

    public String toString() {
        return String.format("at %s x Original Stop Loss size", this.Multiplicator);
    }

    public static Element generate(IRandomGenerator iRandomGenerator, ATMGenerateConfig aTMGenerateConfig) {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "MultipleOfOriginalSL");
        element.setAttribute("use", "true");
        double d = iRandomGenerator.nextDouble(aTMGenerateConfig.slMultipleMin, aTMGenerateConfig.slMultipleMax, 0.05, 2);
        XMLUtil.setItemDoubleParam((Element)element, (String)"Multiplicator", (double)d);
        return element;
    }
}

