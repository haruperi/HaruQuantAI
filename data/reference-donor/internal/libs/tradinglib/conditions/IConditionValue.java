/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.lib.utils.ISQCloneable;

public interface IConditionValue
extends ISQCloneable<IConditionValue> {
    public static final String AdditionalMarket = "AdditionalMarket";
    public static final String SampleType = "SampleType";

    public double getValue(Object ... var1) throws Exception;

    public double getStatsValue(Object ... var1) throws Exception;

    public String getLabel(Object ... var1) throws Exception;

    public String getTitle() throws Exception;

    public String getConditionParamValue(String var1, String var2);

    public String getCrossCheckSettingName();

    public boolean statsExists(Object ... var1);

    public String printFormatedValue(double var1) throws Exception;
}

