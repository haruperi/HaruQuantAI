/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckConditionValue;

public class Condition
implements ISQCloneable<Condition> {
    private boolean use;
    private IConditionValue leftSide;
    private IConditionValue rightSide;
    private String comparator;
    private double leftStatsValue;
    private double rightStatsValue;

    public Condition(boolean bl, IConditionValue iConditionValue, IConditionValue iConditionValue2, String string) {
        this.use = bl;
        this.leftSide = iConditionValue;
        this.rightSide = iConditionValue2;
        this.comparator = string;
    }

    public Condition getClone() throws Exception {
        return new Condition(this.use, (IConditionValue)this.leftSide.getClone(), (IConditionValue)this.rightSide.getClone(), this.comparator);
    }

    public boolean isMet(Object ... objectArray) throws Exception {
        if (this.leftSide == null || this.rightSide == null) {
            return true;
        }
        if (!this.leftSide.statsExists(objectArray) || !this.rightSide.statsExists(objectArray)) {
            return true;
        }
        double d = SQUtils.round2((double)this.leftSide.getValue(objectArray));
        double d2 = SQUtils.round2((double)this.rightSide.getValue(objectArray));
        this.leftStatsValue = this.leftSide.getStatsValue(objectArray);
        this.rightStatsValue = this.rightSide.getStatsValue(objectArray);
        if (!this.use) {
            return false;
        }
        return Condition.validate(d - d2, this.comparator);
    }

    public boolean isMet(ResultsGroup resultsGroup, Object object, Object object2) throws Exception {
        if (this.leftSide == null || this.rightSide == null) {
            return true;
        }
        if (!this.leftSide.statsExists(resultsGroup, object) || !this.rightSide.statsExists(resultsGroup, object2)) {
            return true;
        }
        double d = SQUtils.round2((double)this.leftSide.getValue(resultsGroup, object));
        double d2 = SQUtils.round2((double)this.rightSide.getValue(resultsGroup, object2));
        this.leftStatsValue = this.leftSide.getStatsValue(resultsGroup, object);
        this.rightStatsValue = this.rightSide.getStatsValue(resultsGroup, object2);
        if (!this.use) {
            return false;
        }
        return Condition.validate(d - d2, this.comparator);
    }

    public static boolean validate(double d, String string) throws Exception {
        switch (string) {
            case ">": {
                return d > 0.0;
            }
            case "<": {
                return d < 0.0;
            }
            case "=": {
                return d == 0.0;
            }
            case ">=": {
                return d >= 0.0;
            }
            case "<=": {
                return d <= 0.0;
            }
            case "<>": {
                return d != 0.0;
            }
        }
        throw new Exception(L.t((String)"Unknown comparator '%s'", (Object[])new Object[]{string}));
    }

    public String getAsText(Object ... objectArray) throws Exception {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(this.leftSide.getLabel(objectArray));
        stringBuilder.append(" ");
        stringBuilder.append(this.comparator);
        stringBuilder.append(" ");
        stringBuilder.append(this.rightSide.getLabel(objectArray));
        return stringBuilder.toString();
    }

    public String getAsText(ResultsGroup resultsGroup, Object object, Object object2) throws Exception {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(this.leftSide.getLabel(resultsGroup, object));
        stringBuilder.append(" ");
        stringBuilder.append(this.comparator);
        stringBuilder.append(" ");
        stringBuilder.append(this.rightSide.getLabel(resultsGroup, object2));
        return stringBuilder.toString();
    }

    public String toString() {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(this.leftSide.toString());
        stringBuilder.append(" ");
        stringBuilder.append(this.comparator);
        stringBuilder.append(" ");
        stringBuilder.append(this.rightSide.toString());
        return stringBuilder.toString();
    }

    public double getLeftStatsValue() {
        return this.leftStatsValue;
    }

    public double getRightStatsValue() {
        return this.rightStatsValue;
    }

    public IConditionValue getLeftSideConditionValue() {
        return this.leftSide;
    }

    public IConditionValue getRightSideConditionValue() {
        return this.rightSide;
    }

    public boolean isUsed() {
        return this.use;
    }

    public boolean isFitnessCondition() {
        return this.leftSide.toString().contains("Fitness") || this.rightSide.toString().contains("Fitness");
    }

    public boolean isCrossCheckCondition() {
        return CrossCheckConditionValue.class.isAssignableFrom(this.leftSide.getClass()) || CrossCheckConditionValue.class.isAssignableFrom(this.rightSide.getClass());
    }

    public boolean isCrossCheckCondition(String string) {
        return this.leftSide.getCrossCheckSettingName() != null && this.leftSide.getCrossCheckSettingName().contains(string) || this.rightSide.getCrossCheckSettingName() != null && this.rightSide.getCrossCheckSettingName().contains(string);
    }

    public boolean isPortfolioCondition() {
        return this.leftSide.toString().contains("Portfolio") || this.rightSide.toString().contains("Portfolio");
    }
}

