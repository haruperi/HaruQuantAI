/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;

public class WorstDailyEquity {
    public void compute(ResultsGroup resultsGroup) throws Exception {
        Result result = resultsGroup.portfolio();
        Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
        if (long2FloatRBTreeMap == null || long2FloatRBTreeMap.isEmpty()) {
            return;
        }
        OrdersList ordersList = resultsGroup.orders();
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            order.worstDailyEquity = this.getWorstEquity(order.OpenTime, order.CloseTime, long2FloatRBTreeMap);
        }
    }

    private float getWorstEquity(long l, long l2, Long2FloatRBTreeMap long2FloatRBTreeMap) {
        float f = 0.0f;
        long l3 = l;
        boolean bl = true;
        while (true) {
            long l4;
            if (long2FloatRBTreeMap.containsKey(l4 = l3) && (bl || long2FloatRBTreeMap.get(l4) < f)) {
                f = long2FloatRBTreeMap.get(l4);
                bl = false;
            }
            if (l3 > l2) break;
            l3 = SQTime.addDays((long)l3, (int)1);
        }
        return f;
    }
}

