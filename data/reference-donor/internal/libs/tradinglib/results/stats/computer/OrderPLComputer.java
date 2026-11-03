/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results.stats.computer;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.results.SymbolInfo;
import com.strategyquant.tradinglib.results.SymbolsMap;
import com.strategyquant.tradinglib.results.stats.computer.IOrderComputer;
import java.io.Serializable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OrderPLComputer
implements IOrderComputer,
Serializable {
    public static final Logger Log = LoggerFactory.getLogger((String)"OrderPLComputer");

    @Override
    public void compute(OrdersList ordersList, SettingsMap settingsMap, SymbolsMap symbolsMap) throws Exception {
        double d;
        double d2 = d = settingsMap.getDouble("MoneyManagement.InitialCapital", 10000.0);
        boolean bl = settingsMap.getBoolean("AddCommissionSwapToPL", false);
        float f = 0.0f;
        InstrumentInfo instrumentInfo = symbolsMap.getDefaultInstrumentInfo();
        for (int i = 0; i < ordersList.size(); ++i) {
            InstrumentInfo instrumentInfo2;
            Order order = ordersList.get(i);
            if (instrumentInfo != null) {
                instrumentInfo2 = instrumentInfo;
            } else {
                SymbolInfo symbolInfo = symbolsMap.get(order.Symbol);
                if (symbolInfo == null) {
                    throw new Exception("Symbol info data not found for symbol: '" + order.Symbol + "' for order " + order.toString());
                }
                instrumentInfo2 = symbolInfo.InstrumentInfo();
            }
            order.PipsPL = order.Type == 9 || order.Type == 10 ? 0.0f : (float)this.computeOrderPLInTicks(order, instrumentInfo2.tickSize);
            if (order.Type != 9 && order.Type != 10) {
                order.PL = (float)this.computeOrderPLInMoney(order, instrumentInfo2.tickSize, instrumentInfo2.pointValue);
                order.CommSwapApplied = false;
            }
            if (order.PL == -1.0E8f) {
                order.PL = 0.0f;
            }
            if (bl && !order.CommSwapApplied) {
                order.PL += order.CommSwap;
                order.PL -= order.SlippageInMoney;
                order.CommSwapApplied = true;
            }
            order.PctPL = (float)OrderPLComputer.getPercentagePL(order.PL, d);
            if (order.PL > 0.0f && order.PctPL < 0.0f) {
                order.PctPL = -order.PctPL;
            }
            if (order.PL < 0.0f && order.PctPL > 0.0f) {
                order.PctPL = -order.PctPL;
            }
            order.AccountBalance = (float)(d2 += (double)order.PL);
            order.PctAccountBalance = f += order.PctPL;
            long l = (order.CloseTime - order.OpenTime) / 1000L;
            order.Duration = (int)(l < Integer.MAX_VALUE ? l : Integer.MAX_VALUE);
            if (instrumentInfo2 == null) continue;
            if (order.PipsMAE != 0.0f) {
                order.MAE = (float)((double)(order.Size * order.PipsMAE) * instrumentInfo2.pointValue * instrumentInfo2.tickSize);
            }
            if (order.PipsMFE == 0.0f) continue;
            order.MFE = (float)((double)(order.Size * order.PipsMFE) * instrumentInfo2.pointValue * instrumentInfo2.tickSize);
        }
        this.endCompute(ordersList, settingsMap, symbolsMap);
    }

    public double computeOrderPLInMoney(Order order, double d, double d2) {
        return (double)(order.PipsPL * order.Size) * d2 * d;
    }

    public double computeOrderPLInTicks(Order order, double d) {
        if (order.Type == 1) {
            return SQUtils.round2((double)((double)(order.ClosePrice - order.OpenPrice) / d));
        }
        if (order.Type == 2) {
            return SQUtils.round2((double)((double)(order.OpenPrice - order.ClosePrice) / d));
        }
        return 0.0;
    }

    public static double getPercentagePL(double d, double d2) {
        if (d2 == 0.0) {
            return 0.0;
        }
        return 100.0 * d / d2;
    }

    private void endCompute(OrdersList ordersList, SettingsMap settingsMap, SymbolsMap symbolsMap) throws Exception {
        float f = 1.0f;
        float f2 = 0.0f;
        float f3 = 0.0f;
        for (int i = 0; i < ordersList.size(); ++i) {
            float f4;
            Order order = ordersList.get(i);
            if (order.Type == 9 || order.Type == 10) continue;
            float f5 = 1.0f + order.PctPL / 100.0f;
            f = f4 = f5 * f;
            f3 = (f4 - 1.0f) * 100.0f;
            order.PctPL_TWR = f3 - f2;
            f2 = f3;
            order.PL = (float)SQUtils.round2((double)order.PL);
            order.PctPL_TWR = order.PctPL_TWR;
            order.PipsPL = (float)SQUtils.round2((double)order.PipsPL);
        }
    }
}

