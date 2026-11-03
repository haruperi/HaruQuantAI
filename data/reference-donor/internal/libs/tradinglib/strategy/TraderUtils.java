/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Trader;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;

public class TraderUtils {
    public static OrdersList getHistoryOrders(Trader trader) {
        return trader.getHistoryOrders();
    }

    public static Long2FloatRBTreeMap getWorstDailyEquity(Trader trader) {
        return trader.getWorstDailyEquity();
    }
}

