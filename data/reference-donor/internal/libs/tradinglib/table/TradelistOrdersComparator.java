/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.StringComparator
 */
package com.strategyquant.tradinglib.table;

import com.strategyquant.lib.utils.StringComparator;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.TradelistColumn;
import java.util.Comparator;

public class TradelistOrdersComparator
implements Comparator<Order> {
    private TradelistColumn column;
    private boolean asc;

    @Override
    public int compare(Order order, Order order2) {
        Object object = "";
        Object object2 = "";
        try {
            double d;
            object = this.column.getValue(order);
            object2 = this.column.getValue(order2);
            switch (this.column.getType()) {
                case "Text": {
                    StringComparator stringComparator = new StringComparator();
                    int n = stringComparator.compare(String.valueOf(object), String.valueOf(object2));
                    if (this.asc) {
                        return n;
                    }
                    return -1 * n;
                }
                case "Time": {
                    long l = (Long)object;
                    long l2 = (Long)object2;
                    if (l < l2) {
                        if (this.asc) {
                            return -1;
                        }
                        return 1;
                    }
                    if (l > l2) {
                        if (this.asc) {
                            return 1;
                        }
                        return -1;
                    }
                    return 0;
                }
                case "Integer": {
                    int n = (Integer)object;
                    int n2 = (Integer)object2;
                    if (n < n2) {
                        if (this.asc) {
                            return -1;
                        }
                        return 1;
                    }
                    if (n > n2) {
                        if (this.asc) {
                            return 1;
                        }
                        return -1;
                    }
                    return 0;
                }
            }
            if (object instanceof Float) {
                float f;
                float f2 = ((Float)object).floatValue();
                if (f2 < (f = ((Float)object2).floatValue())) {
                    if (this.asc) {
                        return -1;
                    }
                    return 1;
                }
                if (f2 > f) {
                    if (this.asc) {
                        return 1;
                    }
                    return -1;
                }
                return 0;
            }
            double d2 = (Double)object;
            if (d2 < (d = ((Double)object2).doubleValue())) {
                if (this.asc) {
                    return -1;
                }
                return 1;
            }
            if (d2 > d) {
                if (this.asc) {
                    return 1;
                }
                return -1;
            }
            return 0;
        }
        catch (Exception exception) {
            StringComparator stringComparator = new StringComparator();
            int n = stringComparator.compare(String.valueOf(object), String.valueOf(object2));
            if (this.asc) {
                return n;
            }
            return -1 * n;
        }
    }

    public TradelistColumn getColumn() {
        return this.column;
    }

    public void setColumn(TradelistColumn tradelistColumn) {
        this.column = tradelistColumn;
    }

    public boolean isAsc() {
        return this.asc;
    }

    public void setAsc(boolean bl) {
        this.asc = bl;
    }
}

