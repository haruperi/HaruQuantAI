/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.generator;

import com.strategyquant.tradinglib.Negater;
import com.strategyquant.tradinglib.SortOrder;
import java.util.Comparator;

public class NegaterComparatorByOrder
implements Comparator<Negater> {
    @Override
    public int compare(Negater negater, Negater negater2) {
        int n;
        int n2 = this.getOrder(negater);
        if (n2 > (n = this.getOrder(negater2))) {
            return 1;
        }
        if (n2 < n) {
            return -1;
        }
        return 0;
    }

    private int getOrder(Negater negater) {
        Class<?> clazz = negater.getClass();
        SortOrder sortOrder = clazz.getAnnotation(SortOrder.class);
        if (sortOrder == null) {
            return 100;
        }
        return sortOrder.value();
    }
}

