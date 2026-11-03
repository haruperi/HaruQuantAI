/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import java.io.Serializable;

public class WFSimulationJobResult
implements Serializable {
    private Object durationStats;
    private String dismissalMessage;
    private int dismissalReason;
    private OrdersList orders;
    private int index;

    public WFSimulationJobResult(OrdersList ordersList, int n, DurationStats durationStats) {
        this.orders = ordersList;
        this.index = n;
        this.durationStats = durationStats;
    }

    public WFSimulationJobResult(String string, int n, DurationStats durationStats) {
        this.dismissalMessage = string;
        this.dismissalReason = n;
        this.durationStats = durationStats;
    }

    public OrdersList getOrders() {
        return this.orders;
    }

    public int getIndex() {
        return this.index;
    }
}

