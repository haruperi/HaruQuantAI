/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  org.jdom2.Element
 */
package com.strategyquant.tradinglib.atm.exits;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.tradinglib.ExitMethod;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import org.jdom2.Element;

public abstract class AbstractExitLevel
extends ExitMethod {
    protected int exitIndex = 0;

    public AbstractExitLevel(Element element, int n) {
        this.exitIndex = n;
    }

    public abstract void setForOrder(ILiveOrder var1, StrategyBase var2, double var3, double var5) throws TradingException;

    public abstract Element getXML();

    public abstract double getNettingPrice(StrategyBase var1, ILiveOrder var2, double var3, double var5) throws TradingException;

    public void onBarOpen(StrategyBase strategyBase, ILiveOrder iLiveOrder, ILiveOrder iLiveOrder2, double d, double d2) throws TradingException {
    }

    @Override
    public double computeValue(byte by, StrategyBase strategyBase, String string, double d) throws TradingException {
        throw new TradingException("Method shouldn't be called (ATM)!");
    }

    @Override
    public void setForOrder(ILiveOrder iLiveOrder, StrategyBase strategyBase) throws TradingException {
        throw new TradingException("Method shouldn't be called (ATM)!");
    }

    protected void setStrategy(StrategyBase strategyBase) {
        this.Strategy = strategyBase;
    }

    protected void setNewPT(ILiveOrder iLiveOrder, double d, double d2) throws TradingException {
        if (d == d2) {
            return;
        }
        if ((d = this.correctSLPT(iLiveOrder, d, false)) != 0.0) {
            iLiveOrder.setPT(d).Send();
            iLiveOrder.setExitIndex((byte)this.exitIndex);
            if (!iLiveOrder.isSuccessful()) {
                iLiveOrder.Close((byte)8);
            }
        }
    }
}

