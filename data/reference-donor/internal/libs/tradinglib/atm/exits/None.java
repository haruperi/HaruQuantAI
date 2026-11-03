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
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.atm.ATMGenerateConfig;
import com.strategyquant.tradinglib.atm.exits.AbstractExitLevel;
import org.jdom2.Element;

public class None
extends AbstractExitLevel {
    private boolean LimitExitAfterBars;
    private int MaxBars;
    private boolean active = true;

    public None(Element element, int n) throws Exception {
        super(element, n);
        this.LimitExitAfterBars = XMLUtil.getItemBoolParam((Element)element, (String)"LimitExitAfterBars", (boolean)false);
        this.MaxBars = XMLUtil.getItemIntParam((Element)element, (String)"MaxBars", (int)50);
    }

    @Override
    public Element getXML() {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "None");
        XMLUtil.setItemBoolParam((Element)element, (String)"LimitExitAfterBars", (boolean)this.LimitExitAfterBars);
        XMLUtil.setItemIntParam((Element)element, (String)"MaxBars", (int)this.MaxBars);
        return element;
    }

    @Override
    public void setForOrder(final ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, double d2) throws TradingException {
        if (this.LimitExitAfterBars && this.MaxBars > 0) {
            iLiveOrder.registerEvent(2, new IActionEventListener(){
                final /* synthetic */ None this$0;
                {
                    this.this$0 = none;
                }

                @Override
                public void OnActionEvent(StrategyBase strategyBase) throws TradingException {
                    if (this.this$0.checkExitAfterBars(iLiveOrder)) {
                        iLiveOrder.Close((byte)19);
                        iLiveOrder.setExitIndex((byte)this.this$0.exitIndex);
                    }
                }
            });
        }
    }

    public boolean checkExitAfterBars(ILiveOrder iLiveOrder) throws TradingException {
        if (!this.active || iLiveOrder.isClosedOrder()) {
            return false;
        }
        return this.LimitExitAfterBars && this.MaxBars > 0 && iLiveOrder.isMarketOrder() && iLiveOrder.getBarsInTrade() >= this.MaxBars;
    }

    @Override
    public double getNettingPrice(StrategyBase strategyBase, ILiveOrder iLiveOrder, double d, double d2) throws TradingException {
        return -9.9999999E7;
    }

    public void deactivate() {
        this.active = false;
    }

    public String toString() {
        if (this.LimitExitAfterBars) {
            return String.format("by Exit rule - limit to max. %d bars", this.MaxBars);
        }
        return "by Exit rule";
    }

    public static Element generate(IRandomGenerator iRandomGenerator, ATMGenerateConfig aTMGenerateConfig) {
        Element element = new Element("ExitLevel");
        element.setAttribute("key", "None");
        element.setAttribute("use", "true");
        boolean bl = iRandomGenerator.nextBool();
        int n = iRandomGenerator.nextInt(aTMGenerateConfig.noneMinBars, aTMGenerateConfig.noneMaxBars, 1);
        XMLUtil.setItemBoolParam((Element)element, (String)"LimitExitAfterBars", (boolean)bl);
        XMLUtil.setItemIntParam((Element)element, (String)"MaxBars", (int)n);
        return element;
    }
}

