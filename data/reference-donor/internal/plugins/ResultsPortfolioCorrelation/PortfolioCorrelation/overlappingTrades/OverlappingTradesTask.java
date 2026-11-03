/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades;

import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingResult;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTrades;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.concurrent.Callable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OverlappingTradesTask
implements Callable<OverlappingResult> {
    private static final Logger Log = LoggerFactory.getLogger(OverlappingTradesTask.class);
    private ResultsGroup strategy;
    private String symbol1;
    private String symbol2;
    private OverlappingTrades computer = new OverlappingTrades();
    private OrdersList orders1;
    private OrdersList orders2;

    public OverlappingTradesTask(String symbol1, String symbol2, ResultsGroup strategy) {
        this.symbol1 = symbol1;
        this.symbol2 = symbol2;
        this.orders1 = null;
        this.orders2 = null;
        this.strategy = strategy;
    }

    @Override
    public OverlappingResult call() throws Exception {
        this.createOrdersFromStrategy();
        return this.computer.compute(this.strategy, this.symbol1, this.symbol2, this.orders1, this.orders2);
    }

    private void createOrdersFromStrategy() throws Exception {
        this.orders1 = new OrdersList("O1");
        this.orders2 = new OrdersList("O2");
        OrdersList allOrders = this.strategy.orders();
        int symbol1Hash = this.symbol1.hashCode();
        int symbol2Hash = this.symbol2.hashCode();
        for (int i = 0; i < allOrders.size(); ++i) {
            Order o = allOrders.get(i);
            if (!o.isRealOrder()) continue;
            if (o.SetupName.hashCode() == symbol1Hash) {
                this.orders1.add(o);
                continue;
            }
            if (o.SetupName.hashCode() != symbol2Hash) continue;
            this.orders2.add(o);
        }
    }
}

