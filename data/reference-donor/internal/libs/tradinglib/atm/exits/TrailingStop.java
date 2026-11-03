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
import com.strategyquant.tradinglib.IActionEventListener;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import com.strategyquant.tradinglib.atm.exits.helpers.TrailingFormula;
import com.strategyquant.tradinglib.exit.TrailingStopHandler;
import org.jdom2.Element;

public class TrailingStop
extends AbstractExitLevel {
    private int Type;
    private int FixedPips;
    private double AtrMultiplicator;
    private int AtrPeriod;
    public IFormula TrailingStop;
    private double trailingSL = -9.9999999E7;
    private boolean debugTrailingStops = false;

    public TrailingStop(Element element, int n) throws Exception {
        super(element, n);
        this.Type = XMLUtil.getItemIntParam((Element)element, (String)"Type", (int)1);
        this.FixedPips = XMLUtil.getItemIntParam((Element)element, (String)"FixedPips", (int)50);
        this.AtrMultiplicator = XMLUtil.getItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)1.2);
        this.AtrPeriod = XMLUtil.getItemIntParam((Element)element, (String)"AtrPeriod", (int)20);
        this.TrailingStop = new TrailingFormula(this.Type, this.FixedPips, this.AtrMultiplicator, this.AtrPeriod);
    }

    @Override
    public Element getXML() {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "TrailingStop");
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)this.Type);
        XMLUtil.setItemIntParam((Element)element, (String)"FixedPips", (int)this.FixedPips);
        XMLUtil.setItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)this.AtrMultiplicator);
        XMLUtil.setItemIntParam((Element)element, (String)"AtrPeriod", (int)this.AtrPeriod);
        return element;
    }

    @Override
    public void setForOrder(final ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, double d2) throws TradingException {
        if (iLiveOrder.isFilled()) {
            this.setStrategy(strategyBase);
            if (this.TrailingStop != null && !this.TrailingStop.isNoneValue()) {
                this.trailingSL = -9.9999999E7;
                iLiveOrder.registerEvent(2, new IActionEventListener(){
                    final /* synthetic */ TrailingStop this$0;
                    {
                        this.this$0 = trailingStop;
                    }

                    @Override
                    public void OnActionEvent(StrategyBase strategyBase) throws TradingException {
                        this.this$0.trailingSL = TrailingStopHandler.checkTrailingStop(iLiveOrder, this.this$0.TrailingStop, null, strategyBase, this.this$0.trailingSL, this.this$0.debugTrailingStops, (byte)this.this$0.exitIndex);
                    }
                });
            }
        }
    }

    @Override
    public double getNettingPrice(StrategyBase strategyBase, ILiveOrder iLiveOrder, double d, double d2) throws TradingException {
        return TrailingStopHandler.calculatePrice(iLiveOrder, this.TrailingStop, null, strategyBase);
    }

    public String toString() {
        if (this.Type == 1) {
            return String.format("at trailing stop %d pips", this.FixedPips);
        }
        return String.format("at trailing stop %s * ATR(%d)", this.AtrMultiplicator, this.AtrPeriod);
    }

    public static Element generate(IRandomGenerator iRandomGenerator, ATMGenerateConfig aTMGenerateConfig) {
        int n;
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "TrailingStop");
        element.setAttribute("use", "true");
        int n2 = 50;
        double d = 1.2;
        int n3 = 20;
        if (iRandomGenerator.nextBool()) {
            n = 1;
            n2 = iRandomGenerator.nextInt(aTMGenerateConfig.tsFixedPipsMin, aTMGenerateConfig.tsFixedPipsMax, 1);
        } else {
            n = 2;
            d = iRandomGenerator.nextDouble(aTMGenerateConfig.tsATRMutliplierMin, aTMGenerateConfig.tsATRMutliplierMax, 0.05, 2);
            n3 = iRandomGenerator.nextInt(aTMGenerateConfig.tsATRPeriodMin, aTMGenerateConfig.tsATRPeriodMax, 1);
        }
        XMLUtil.setItemIntParam((Element)element, (String)"Type", (int)n);
        XMLUtil.setItemIntParam((Element)element, (String)"FixedPips", (int)n2);
        XMLUtil.setItemDoubleParam((Element)element, (String)"AtrMultiplicator", (double)d);
        XMLUtil.setItemIntParam((Element)element, (String)"AtrPeriod", (int)n3);
        return element;
    }
}

