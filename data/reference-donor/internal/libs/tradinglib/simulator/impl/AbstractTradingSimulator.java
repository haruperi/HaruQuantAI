/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import com.strategyquant.tradinglib.strategy.LiveOrdersCache;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class AbstractTradingSimulator
implements ITradingSimulator {
    public static final Logger Log = LoggerFactory.getLogger((String)"AbstractTradingSimulator");
    protected ReservedBarsType reservedBarsType;
    protected int backtestPrecision = 1;
    protected ChartData mainChartData;
    protected TickEvent tickData;
    protected boolean storePendingOrders = false;
    protected int tradingSymbolHash;
    protected int ambiguousTrades;
    protected LiveOrderObj[] liveOrders = null;
    protected int liveOrdersCount = 0;
    protected boolean realisticGapsHandling = false;
    protected double closingPrice = Double.MIN_VALUE;
    protected boolean isNewBar = false;
    private ITickSimulator tickSimulator;
    private LiveOrdersCache liveOrdersCache = new LiveOrdersCache();

    public AbstractTradingSimulator(ReservedBarsType reservedBarsType, ITickSimulator iTickSimulator) {
        this.reservedBarsType = reservedBarsType;
        this.tickSimulator = iTickSimulator;
    }

    @Override
    public abstract ITradingSimulator clone();

    @Override
    public void initialize() {
    }

    public abstract void eventBarUpdated(int var1);

    protected abstract double getSLPTFilledPrice(double var1, double var3);

    @Override
    public ITickSimulator getTickSimulator() {
        return this.tickSimulator;
    }

    @Override
    public ReservedBarsType getReservedBarsType() {
        return this.reservedBarsType;
    }

    @Override
    public void setTestPrecision(int n) {
        this.backtestPrecision = n;
    }

    @Override
    public int getTestPrecision() {
        return this.backtestPrecision;
    }

    @Override
    public int getAmbiguousTrades() {
        return this.ambiguousTrades;
    }

    @Override
    public void eventNewTick(TickEvent tickEvent, double d, double d2, BarUpdateInfo barUpdateInfo) throws TradingException {
        this.eventNewTick(tickEvent, d, d2);
    }

    @Override
    public boolean getApplyExitsAtTheEndOfRule() {
        return false;
    }

    public LiveOrderObj createLiveOrder(Trader trader, InstrumentInfo instrumentInfo, byte by, String string) {
        return this.liveOrdersCache.createLiveOrder(trader, instrumentInfo, by, string);
    }

    public LiveOrderObj createLiveOrder(Trader trader, InstrumentInfo instrumentInfo, byte by, String string, double d) {
        return this.liveOrdersCache.createLiveOrder(trader, instrumentInfo, by, string, d);
    }

    protected boolean removeOpenTrade(LiveOrderObj liveOrderObj) {
        return this.removeOpenTrade(liveOrderObj, true);
    }

    protected boolean removeOpenTrade(LiveOrderObj liveOrderObj, boolean bl) {
        boolean bl2 = false;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            if (this.liveOrders[i] != liveOrderObj) continue;
            this.removeOpenTradeNoFix(i);
            bl2 = true;
            break;
        }
        if (bl && bl2) {
            this.fixRemovedElements();
        }
        return bl2;
    }

    protected void reuseTemporaryOrder(LiveOrderObj liveOrderObj) {
        this.liveOrdersCache.returnObject(liveOrderObj);
    }

    protected void removeOpenTradeNoFix(int n) {
        if (n >= 0 && n < this.liveOrdersCount) {
            this.liveOrdersCache.returnObject(this.liveOrders[n]);
            this.liveOrders[n] = null;
        }
    }

    protected void fixRemovedElements() {
        int n = -1;
        for (int i = 0; i < this.liveOrdersCount; ++i) {
            if (this.liveOrders[i] == null) continue;
            this.liveOrders[++n] = this.liveOrders[i];
        }
        this.liveOrdersCount = n == -1 ? 0 : n + 1;
    }

    @Override
    public int getOpenOrdersCount(boolean bl) {
        return this.liveOrdersCount;
    }

    @Override
    public ILiveOrder getOpenOrder(int n, boolean bl) {
        if (n < 0 || n >= this.liveOrdersCount) {
            throw new IllegalArgumentException("Trade index is out of range!");
        }
        return this.liveOrders[n];
    }

    @Override
    public void reuseOpenOrder(LiveOrderObj liveOrderObj) {
        Log.info("Returning unsuccess trade");
        this.removeOpenTrade(liveOrderObj);
    }

    protected double priceLevelReached(TickEvent tickEvent, int n, int n2, double d) {
        if (tickEvent.getTime() == -1L) {
            return 0.0;
        }
        if (n2 == 6) {
            if (tickEvent.getBid() <= d) {
                return tickEvent.getBid();
            }
        } else if (n2 == 5) {
            if (tickEvent.getAsk() >= d) {
                return tickEvent.getAsk();
            }
        } else if (n2 == 4) {
            if (tickEvent.getBid() >= d) {
                return tickEvent.getBid();
            }
        } else if (n2 == 3 && tickEvent.getAsk() <= d) {
            return tickEvent.getAsk();
        }
        return 0.0;
    }

    protected double getRealisticSLPTFilledPrice(double d, double d2, TickEvent tickEvent, int n) {
        double d3;
        if (this.realisticGapsHandling && this.isNewBar && (d3 = tickEvent.getBid()) != this.closingPrice && this.isNewBarOnMainSymbolTF(this.tickData)) {
            if (n == 5 || n == 6) {
                Log.debug("GAP detected - prev Close:{}, new Open: {}, realistic fill for MT4 set", (Object)this.closingPrice, (Object)d3);
                return AbstractTradingSimulator.getPriceByType(n, this.tickData.getBid(), this.tickData.getAsk());
            }
            if (n == 3 || n == 4) {
                Log.debug("GAP detected for Limit - prev Close:{}, new Open: {}, realistic fill for MT4 set", (Object)this.closingPrice, (Object)d3);
                double d4 = AbstractTradingSimulator.getPriceByType(n, this.tickData.getBid(), this.tickData.getAsk());
                double d5 = this.getSLPTFilledPrice(d, d2);
                if (n == 3) {
                    return Math.min(d4, d5);
                }
                if (n == 4) {
                    return Math.max(d4, d5);
                }
            }
        }
        return this.getSLPTFilledPrice(d, d2);
    }

    public static double getPriceByType(int n, double d, double d2) {
        if (n == 1 || n == 5 || n == 3 || n == 7) {
            return d2;
        }
        return d;
    }

    protected boolean isNewBarOnMainSymbolTF(TickEvent tickEvent) {
        return this.mainChartData.isNewBarOnMainSymbolTF(tickEvent);
    }

    protected boolean thereWasAGap(byte by, TickEvent tickEvent) {
        double d;
        return this.realisticGapsHandling && this.isNewBar && (by == 5 || by == 6) && (d = tickEvent.getBid()) != this.closingPrice && this.isNewBarOnMainSymbolTF(this.tickData);
    }

    protected void fixMAEMFEByRealPrice(LiveOrderObj liveOrderObj) {
        boolean bl;
        double d = liveOrderObj.isLong() ? liveOrderObj.getClosePrice() - liveOrderObj.getOpenPrice() : liveOrderObj.getOpenPrice() - liveOrderObj.getClosePrice();
        boolean bl2 = bl = d > 0.0;
        if (bl && (double)liveOrderObj.getMFE() < d) {
            liveOrderObj.setMFE((float)d);
        }
        d *= -1.0;
        if (!bl && (double)liveOrderObj.getMAE() < d) {
            liveOrderObj.setMAE((float)d);
        }
    }

    protected double getATR(StrategyBase strategyBase, String string) throws TradingException {
        ChartData chartData = strategyBase.MarketData.Chart(string);
        double d = strategyBase.getATRValue(chartData, 14, 0);
        return d;
    }
}

