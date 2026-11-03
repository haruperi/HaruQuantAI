/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.moneymanagement;

import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.SortOrder;
import java.util.Comparator;

public class MMComparatorByOrder
implements Comparator<MoneyManagementMethod> {
    @Override
    public int compare(MoneyManagementMethod moneyManagementMethod, MoneyManagementMethod moneyManagementMethod2) {
        int n;
        int n2 = this.getOrder(moneyManagementMethod);
        if (n2 > (n = this.getOrder(moneyManagementMethod2))) {
            return 1;
        }
        if (n2 < n) {
            return -1;
        }
        return 0;
    }

    private int getOrder(MoneyManagementMethod moneyManagementMethod) {
        Class<?> clazz = moneyManagementMethod.getClass();
        SortOrder sortOrder = clazz.getAnnotation(SortOrder.class);
        if (sortOrder == null) {
            return 100000;
        }
        return sortOrder.value();
    }
}

