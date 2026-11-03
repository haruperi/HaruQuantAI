/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades;

import com.strategyquant.lib.SQTime;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingResult;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTrade;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;

public class OverlappingTrades {
    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public OverlappingResult compute(ResultsGroup strategy, String symbol1, String symbol2, OrdersList orders1, OrdersList orders2) throws Exception {
        try {
            OverlappingResult result = new OverlappingResult(symbol1, symbol2);
            int count = 0;
            String overlappedTime = "N/A";
            for (int i = 0; i < orders1.size(); ++i) {
                Order order1 = orders1.get(i);
                if (!order1.isRealOrder()) continue;
                for (int j = 0; j < orders2.size(); ++j) {
                    Order order2 = orders2.get(j);
                    if (!order2.isRealOrder() || order1.OpenTime >= order2.CloseTime || order1.CloseTime <= order2.OpenTime) continue;
                    long from = order1.OpenTime > order2.OpenTime ? order1.OpenTime : order2.OpenTime;
                    long to = order1.CloseTime < order2.CloseTime ? order1.CloseTime : order2.CloseTime;
                    overlappedTime = SQTime.formatDateTime((long)((int)((to - from) / 1000L)));
                    result.data.add(new OverlappingTrade(order1.OpenTime, order1.CloseTime, order2.OpenTime, order2.CloseTime, overlappedTime));
                    ++count;
                }
            }
            result.count = count;
            OverlappingResult overlappingResult = result;
            return overlappingResult;
        }
        finally {
            orders1.clear();
            orders2.clear();
        }
    }
}

