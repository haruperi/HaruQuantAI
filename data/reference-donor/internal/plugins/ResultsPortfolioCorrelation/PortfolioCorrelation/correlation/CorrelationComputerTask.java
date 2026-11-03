/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.correlation.CorrelationComputer
 *  com.strategyquant.tradinglib.correlation.CorrelationPeriods
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation;

import com.strategyquant.lib.L;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation.CorrelationResult;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.correlation.CorrelationComputer;
import com.strategyquant.tradinglib.correlation.CorrelationPeriods;
import java.util.concurrent.Callable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CorrelationComputerTask
implements Callable<CorrelationResult> {
    private static final Logger Log = LoggerFactory.getLogger(CorrelationComputerTask.class);
    private ResultsGroup strategy;
    private String symbol1;
    private String symbol2;
    private int period;
    private CorrelationType type;
    private boolean allowNegativeCorrelation;
    private boolean addEmptyPeriods;
    private CorrelationComputer computer = new CorrelationComputer();
    private OrdersList orders1;
    private OrdersList orders2;
    private CorrelationPeriods periods;

    public CorrelationComputerTask(ResultsGroup strategy, String symbol1, String symbol2, int period, CorrelationType type, boolean allowNegativeCorrelation, boolean addEmptyPeriods, CorrelationPeriods periods) {
        this.strategy = strategy;
        this.symbol1 = symbol1;
        this.symbol2 = symbol2;
        this.orders1 = null;
        this.orders2 = null;
        this.period = period;
        this.type = type;
        this.allowNegativeCorrelation = allowNegativeCorrelation;
        this.addEmptyPeriods = addEmptyPeriods;
        this.periods = periods;
    }

    @Override
    public CorrelationResult call() throws Exception {
        try {
            this.createOrdersFromStrategy();
            if (this.orders1 == null || this.orders1.size() == 0 || this.orders2 == null || this.orders2.size() == 0) {
                CorrelationResult correlationResult = null;
                return correlationResult;
            }
            CorrelationResult result = new CorrelationResult(this.symbol1, this.symbol2);
            result.value = this.computer.computeCorrelation(this.addEmptyPeriods, this.symbol1, this.symbol2, this.orders1, this.orders2, this.periods, this.type);
            if (result.value == -99.0) {
                throw new Exception(L.t((String)"Cannot get values for computing correlation.", (Object[])new Object[0]));
            }
            CorrelationResult correlationResult = result;
            return correlationResult;
        }
        catch (Exception e) {
            Log.error("Error while computing portfolio correlation.", (Throwable)e);
            throw e;
        }
        finally {
            this.orders1 = null;
            this.orders2 = null;
        }
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

