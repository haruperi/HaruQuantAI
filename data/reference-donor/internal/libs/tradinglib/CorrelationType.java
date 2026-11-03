/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TimePeriods
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TimePeriods;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.debug.Debugger;
import java.lang.reflect.Constructor;

public abstract class CorrelationType
extends Debugger
implements ISQCloneable<CorrelationType> {
    public static final int DATA_TYPE_PL = 5;
    public static final int DATA_TYPE_TRADES = 10;
    protected String name = null;
    protected int dataType = -1;

    public String getName() {
        return this.name;
    }

    public int getDataType() {
        return this.dataType;
    }

    public String toString() {
        return this.name;
    }

    public abstract void computePeriods(OrdersList var1, int var2, TimePeriods var3) throws Exception;

    public boolean isCanceledOrder(Order order) {
        return order.isCanceledOrder() && order.PL == 0.0f;
    }

    public boolean shouldSkipPeriod(double d, double d2) {
        return false;
    }

    public CorrelationType getClone() {
        try {
            Constructor<?> constructor = null;
            constructor = this.getClass().getConstructor(new Class[0]);
            CorrelationType correlationType = (CorrelationType)SQUtils.invokeUnchecked(constructor, (Object[])new Object[0]);
            correlationType.name = this.name;
            correlationType.dataType = this.dataType;
            return correlationType;
        }
        catch (NoSuchMethodException | SecurityException exception) {
            throw new IllegalArgumentException("Exception cloning CorrelationType!", exception);
        }
    }
}

