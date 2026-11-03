/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results.stats.comparator;

import com.strategyquant.tradinglib.Order;
import java.util.Comparator;

public class OrderComparatorByCloseTime
implements Comparator<Order> {
    @Override
    public int compare(Order order, Order order2) {
        if (order.CloseTime < order2.CloseTime) {
            return -1;
        }
        if (order.CloseTime > order2.CloseTime) {
            return 1;
        }
        return 0;
    }
}

