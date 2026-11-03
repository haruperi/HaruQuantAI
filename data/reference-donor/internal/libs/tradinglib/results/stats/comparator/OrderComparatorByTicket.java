/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results.stats.comparator;

import com.strategyquant.tradinglib.Order;
import java.util.Comparator;

public class OrderComparatorByTicket
implements Comparator<Order> {
    @Override
    public int compare(Order order, Order order2) {
        if (order.Ticket < order2.Ticket) {
            return -1;
        }
        if (order.Ticket > order2.Ticket) {
            return 1;
        }
        return 0;
    }
}

