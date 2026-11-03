/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.exit;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.IFormula;
import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.simulator.Engines;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TrailingStopHandler {
    public static final Logger Log = LoggerFactory.getLogger((String)"TrailingStop");

    public static double checkTrailingStop(ILiveOrder iLiveOrder, IFormula iFormula, IFormula iFormula2, StrategyBase strategyBase, double d, boolean bl, byte by) throws TradingException {
        double d2;
        if (iLiveOrder.isClosedOrder()) {
            return d;
        }
        if (!iLiveOrder.isMarketOrder()) {
            return d;
        }
        boolean bl2 = strategyBase.getEngine() == 56756755 || strategyBase.getEngine() == 938213070;
        InstrumentInfo instrumentInfo = strategyBase.MarketData.getInstrumentInfo(iLiveOrder.getSymbol());
        double d3 = iLiveOrder.isNettingMode() ? iLiveOrder.getLastOpenPrice() : iLiveOrder.getOpenPrice();
        double d4 = TrailingStopHandler.calculatePrice(iLiveOrder, iFormula, iFormula2, strategyBase);
        if (d4 == -9.9999999E7) {
            return d;
        }
        double d5 = 0.0;
        if (iFormula2 != null) {
            d5 = iFormula2.evaluateFormula(strategyBase, iLiveOrder.getSymbol(), 0.0, 1);
            d5 = d5 == -9.9999999E7 ? 0.0 : d5;
            d5 = bl2 ? SQUtils.adjustToTickSize((double)d5, (double)instrumentInfo.tickStep) : SQUtils.round((double)d5, (int)instrumentInfo.decimals);
        }
        double d6 = d2 = iLiveOrder.getSL() == -9.9999999E7 ? -9.9999999E7 : SQUtils.round((double)iLiveOrder.getSL(), (int)instrumentInfo.decimals);
        if (iLiveOrder.getDirection() == 1) {
            double d7 = SQUtils.round((double)(strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Bid() - d3), (int)instrumentInfo.decimals);
            if (d7 >= d5 && (d2 == -9.9999999E7 || d2 < d4) && TrailingStopHandler.isTrailingStopValid(strategyBase, iLiveOrder, d4)) {
                d4 = SQUtils.fixPrice((double)instrumentInfo.tickStep, (double)d4, (int)instrumentInfo.decimals);
                if (Engines.isTradestationEngine(strategyBase.getEngine())) {
                    if (d4 > d || d == -9.9999999E7) {
                        if (bl) {
                            Log.info(SQTime.toDateMinuteString((long)strategyBase.Time(0)) + " - Order " + iLiveOrder.getOrderId() + " - Moving Long Trailing stop to: {}, orig SL: {}", (Object)d4, (Object)d2);
                        }
                        iLiveOrder.setExitIndex(by);
                        iLiveOrder.setSL((byte)21, d4).Send();
                        d = d4;
                    }
                } else if (d4 > d || d == -9.9999999E7) {
                    if (bl) {
                        Log.info(SQTime.toDateMinuteString((long)strategyBase.Time(0)) + " - Order " + iLiveOrder.getOrderId() + " - Moving Long Trailing stop to: {}, orig SL: {}", (Object)d4, (Object)d2);
                    }
                    iLiveOrder.setExitIndex(by);
                    iLiveOrder.setSL((byte)21, d4).Send();
                    d = d4;
                }
            }
        } else {
            double d8 = SQUtils.round((double)(d3 - strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Ask()), (int)instrumentInfo.decimals);
            if (d8 >= d5 && (d2 == -9.9999999E7 || d2 > d4) && TrailingStopHandler.isTrailingStopValid(strategyBase, iLiveOrder, d4)) {
                d4 = SQUtils.fixPrice((double)instrumentInfo.tickStep, (double)d4);
                if (Engines.isTradestationEngine(strategyBase.getEngine())) {
                    if (d == -9.9999999E7 || d4 < d) {
                        if (bl) {
                            Log.info(SQTime.toDateMinuteString((long)strategyBase.Time(0)) + " - Order " + iLiveOrder.getOrderId() + " - Moving Short Trailing stop to: {}", (Object)d4);
                        }
                        iLiveOrder.setExitIndex(by);
                        iLiveOrder.setSL((byte)21, d4).Send();
                        d = d4;
                    }
                } else if (d == -9.9999999E7 || d4 < d) {
                    if (bl) {
                        Log.info(SQTime.toDateMinuteString((long)strategyBase.Time(0)) + " - Order " + iLiveOrder.getOrderId() + " - Moving Short Trailing stop to: {}", (Object)d4);
                    }
                    iLiveOrder.setExitIndex(by);
                    iLiveOrder.setSL((byte)21, d4).Send();
                }
            }
        }
        return d;
    }

    private static boolean isTrailingStopValid(StrategyBase strategyBase, ILiveOrder iLiveOrder, double d) throws TradingException {
        double d2 = strategyBase.getMinDistance() * strategyBase.MarketData.getInstrumentInfo((String)iLiveOrder.getSymbol()).tickSize;
        return iLiveOrder.isLong() ? d < strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Bid() - d2 : d > strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Ask() + d2;
    }

    public static boolean setExit(ILiveOrder iLiveOrder, StrategyBase strategyBase, double d, boolean bl) throws TradingException {
        if (d == -9.9999999E7) {
            return false;
        }
        if (bl) {
            Log.info(SQTime.toDateMinuteString((long)strategyBase.Time(0)) + " - Creating order for Trailing stop at: {}", (Object)d);
        }
        int n = iLiveOrder.isLong() ? -1 : 1;
        byte by = n > 0 ? (byte)100 : 102;
        ILiveOrder iLiveOrder2 = strategyBase.Trader.Open(by, iLiveOrder.getSymbol(), d).setMagicNumber(iLiveOrder.getMagicNumber()).setSLType((byte)21).Send();
        return true;
    }

    public static double calculatePrice(ILiveOrder iLiveOrder, IFormula iFormula, IFormula iFormula2, StrategyBase strategyBase) throws TradingException {
        boolean bl = strategyBase.getEngine() == 56756755 || strategyBase.getEngine() == 938213070;
        InstrumentInfo instrumentInfo = strategyBase.MarketData.getInstrumentInfo(iLiveOrder.getSymbol());
        double d = iLiveOrder.getDirection() == 1 ? strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Bid() : strategyBase.MarketData.Chart(iLiveOrder.getSymbol()).Ask();
        double d2 = iFormula.evaluateFormula(strategyBase, iLiveOrder.getSymbol(), d, iLiveOrder.getDirection());
        if (d2 == -9.9999999E7) {
            return -9.9999999E7;
        }
        double d3 = 0.0;
        d3 = bl ? SQUtils.adjustToTickSize((double)d2, (double)instrumentInfo.tickStep) : SQUtils.round((double)d2, (int)instrumentInfo.decimals);
        return d3;
    }
}

