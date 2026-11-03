/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.conditions.IConditionValue;

public class NumericValue
implements IConditionValue {
    private double value;

    public NumericValue(double d) {
        this.value = d;
    }

    @Override
    public double getStatsValue(Object ... objectArray) throws Exception {
        return this.value;
    }

    @Override
    public double getValue(Object ... objectArray) {
        return this.value;
    }

    @Override
    public String getLabel(Object ... objectArray) {
        return SQUtils.doubleToString((double)this.value);
    }

    public String toString() {
        return SQUtils.d2((double)this.value);
    }

    public IConditionValue getClone() {
        return new NumericValue(this.value);
    }

    @Override
    public String getTitle() throws Exception {
        return L.t((String)"Number", (Object[])new Object[0]);
    }

    @Override
    public String getCrossCheckSettingName() {
        return null;
    }

    @Override
    public String getConditionParamValue(String string, String string2) {
        return string2;
    }

    @Override
    public boolean statsExists(Object ... objectArray) {
        return true;
    }

    @Override
    public String printFormatedValue(double d) throws Exception {
        return SQUtils.d2((double)d);
    }
}

