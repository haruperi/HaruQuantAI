/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.TradestationSimulator;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MultiChartsSimulator
extends TradestationSimulator {
    public static final Logger Log = LoggerFactory.getLogger((String)"MultiChartsSimulator");
    public static final Logger BacktestLog = LoggerFactory.getLogger((String)"BacktestLog");
    public static final int Engine = 938213070;

    @Override
    public ITradingSimulator clone() {
        MultiChartsSimulator multiChartsSimulator = new MultiChartsSimulator();
        multiChartsSimulator.setTestPrecision(this.getTestPrecision());
        return multiChartsSimulator;
    }

    @Override
    protected void checkSLPT(TickEvent tickEvent, int n, long l, double d, double d2, double d3, BarUpdateInfo barUpdateInfo) {
        LiveOrderObj liveOrderObj = this.findExistingMarketOrder(-1, -1);
        if (liveOrderObj == null) {
            return;
        }
        boolean bl = false;
        boolean bl2 = false;
        double d4 = 0.0;
        double d5 = 0.0;
        for (int i = 0; i < this.exitOrdersCount; ++i) {
            boolean bl3;
            int n2;
            LiveOrderObj liveOrderObj2 = this.exitOrders[i];
            if (liveOrderObj2 == null || liveOrderObj2.getSymbolHash() != n) continue;
            if (!liveOrderObj2.isExitOrder()) {
                throw new IllegalArgumentException("This shouldn't happen");
            }
            if (liveOrderObj2.getBarsInTrade() >= 1) {
                n2 = liveOrderObj2.getOrderType();
                if (n2 == 101) {
                    d4 = liveOrderObj2.getOpenPrice();
                } else if (n2 == 103) {
                    d5 = liveOrderObj2.getOpenPrice();
                }
                this.removeClosingTradeNoFix(i);
                bl2 = true;
                continue;
            }
            n2 = liveOrderObj2.getMagicNumber();
            if (n2 != 0 && n2 != liveOrderObj.getMagicNumber()) continue;
            boolean bl4 = liveOrderObj2.getOrderType() == 102 || liveOrderObj2.getOrderType() == 100;
            boolean bl5 = bl3 = liveOrderObj2.getOrderType() == 103 || liveOrderObj2.getOrderType() == 101;
            if ((!this.useInitialSLPT || !bl4 && !bl3) && liveOrderObj2.getOpenTime() < liveOrderObj.getOpenTime()) continue;
            liveOrderObj2.setTickData(this.tickData.getAsk(), this.tickData.getBid());
            double d6 = this.priceLevelReached(tickEvent, n, liveOrderObj2.getOrderType(), liveOrderObj2.getOpenPrice(), barUpdateInfo);
            if (!(d6 > 0.0) || this.stopLimitShouldBeFilledFirst(tickEvent, n, liveOrderObj2.getOrderType(), liveOrderObj2.getOpenPrice(), barUpdateInfo) || this.otherExitStopShouldBeFilledFirst(tickEvent, i, n, liveOrderObj2.getOrderType(), liveOrderObj2.getOpenPrice(), barUpdateInfo)) continue;
            byte by = liveOrderObj2.getOrderType();
            double d7 = tickEvent.getAsk() - tickEvent.getBid();
            d6 = by == 100 || by == 101 ? this.fixByHighLow(d6, d + d7, d2 + d7) : this.fixByHighLow(d6, d, d2);
            d6 = this.getStopLimitFillPriceMC(d6, barUpdateInfo, liveOrderObj2, liveOrderObj, tickEvent, d4, d5);
            if (barUpdateInfo.eventType != 2) {
                this.tradestationBouncingTicks(tickEvent, this.bouncingTicksPct, d, d2, d3, n, liveOrderObj2.getOrderType(), liveOrderObj2.getInstrumentInfo(), liveOrderObj2.getOpenPrice());
            }
            this.lastFilledPriceThisBar = d6;
            this.closeOrder(liveOrderObj, d6, this.getOrderCloseType(liveOrderObj2.getOrderType()));
            this.removeOpenTrade(liveOrderObj, false);
            bl = true;
            this.removeClosingTradeNoFix(i);
            bl2 = true;
            break;
        }
        if (bl) {
            this.fixRemovedElements();
        }
        if (bl2) {
            this.fixRemovedClosingElements();
        }
    }

    private double priceLevelReached(TickEvent tickEvent, int n, byte by, double d, BarUpdateInfo barUpdateInfo) {
        if (tickEvent.getTime() == -1L) {
            return 0.0;
        }
        if (by == 6 || by == 102) {
            if (tickEvent.getBid() <= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getBid();
                }
                return d;
            }
        } else if (by == 5 || by == 100) {
            if (tickEvent.getAsk() >= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getAsk();
                }
                return d;
            }
        } else if (by == 4 || by == 103) {
            if (tickEvent.getBid() >= d) {
                if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                    return tickEvent.getBid();
                }
                return d;
            }
        } else if ((by == 3 || by == 101) && tickEvent.getAsk() <= d) {
            if (barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                return tickEvent.getAsk();
            }
            return d;
        }
        return 0.0;
    }

    protected double getStopLimitFillPriceMC(double d, BarUpdateInfo barUpdateInfo, LiveOrderObj liveOrderObj, LiveOrderObj liveOrderObj2, TickEvent tickEvent, double d2, double d3) {
        byte by = liveOrderObj.getOrderType();
        if (by == 101) {
            if ((d2 == 0.0 || liveOrderObj.getOpenPrice() != d2) && barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                return tickEvent.getAsk();
            }
            return d;
        }
        if (by == 103) {
            if ((d3 == 0.0 || liveOrderObj.getOpenPrice() != d3) && barUpdateInfo != null && barUpdateInfo.eventType == 2) {
                return tickEvent.getBid();
            }
            return d;
        }
        int n = liveOrderObj.getDirection();
        if (this.lastFilledPriceThisBar <= 0.0) {
            return d;
        }
        if (n > 0) {
            if ((OrderTypes.isStopOrder(by) || OrderTypes.isLimitOrder(by)) && this.lastFilledPriceThisBar > d) {
                return this.lastFilledPriceThisBar;
            }
            if (OrderTypes.isLimitOrder(by) && this.lastFilledPriceThisBar < d) {
                return this.lastFilledPriceThisBar;
            }
        } else if (n < 0) {
            if ((OrderTypes.isStopOrder(by) || OrderTypes.isLimitOrder(by)) && this.lastFilledPriceThisBar < d) {
                return this.lastFilledPriceThisBar;
            }
            if (OrderTypes.isLimitOrder(by) && this.lastFilledPriceThisBar > d) {
                return this.lastFilledPriceThisBar;
            }
        }
        return d;
    }

    @Override
    public int getEngineId() {
        return 938213070;
    }
}

