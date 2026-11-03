/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.conditions;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConditionsChecker {
    public static final Logger Log = LoggerFactory.getLogger((String)"ConditionsChecker");
    public String dismissalMessage;
    public HashMap<String, Object> leftValues = new HashMap();
    public HashMap<String, Object> rightValues = new HashMap();

    public boolean check(ResultsGroup resultsGroup, ArrayList<Condition> arrayList) {
        for (int i = 0; i < arrayList.size(); ++i) {
            Condition condition = arrayList.get(i);
            try {
                if (this.check(resultsGroup, condition)) continue;
                return false;
            }
            catch (CrossCheckDataNotExistException crossCheckDataNotExistException) {
                continue;
            }
            catch (Exception exception) {
                Log.error("Error while checking condition", (Throwable)exception);
                this.dismissalMessage = String.format("Error while evaluating conditions: %s", exception.getMessage());
                return false;
            }
        }
        return true;
    }

    public boolean check(ResultsGroup resultsGroup, Condition condition) throws Exception {
        boolean bl = false;
        this.leftValues.clear();
        this.rightValues.clear();
        byte[] byArray = this.getSampleType(condition.getLeftSideConditionValue());
        byte[] byArray2 = this.getSampleType(condition.getRightSideConditionValue());
        int[] nArray = this.getAdditionalMarket(condition.getLeftSideConditionValue(), resultsGroup);
        int[] nArray2 = this.getAdditionalMarket(condition.getRightSideConditionValue(), resultsGroup);
        for (int i = 0; i < byArray.length; ++i) {
            for (int j = 0; j < byArray2.length; ++j) {
                for (int k = 0; k < nArray.length; ++k) {
                    for (int i2 = 0; i2 < nArray2.length; ++i2) {
                        this.leftValues.put("SampleType", byArray[i]);
                        this.leftValues.put("AdditionalMarket", nArray[k]);
                        this.rightValues.put("SampleType", byArray2[j]);
                        this.rightValues.put("AdditionalMarket", nArray2[i2]);
                        bl = condition.isMet(resultsGroup, this.leftValues, this.rightValues);
                        if (bl) continue;
                        this.dismissalMessage = condition.getAsText(resultsGroup, this.leftValues, this.rightValues);
                        return false;
                    }
                }
            }
        }
        return true;
    }

    public int[] getAdditionalMarket(IConditionValue iConditionValue, ResultsGroup resultsGroup) throws Exception {
        int[] nArray;
        String string = iConditionValue.getCrossCheckSettingName();
        if (string != null && string.equals("RetestOnAdditionalMarkets") && resultsGroup.additionalMarketKeys().size() > 0) {
            byte by = Byte.valueOf(iConditionValue.getConditionParamValue("AdditionalMarket", "0"));
            if (by > 0) {
                nArray = new int[]{by};
            } else {
                List<String> list = resultsGroup.additionalMarketKeys();
                nArray = new int[list.size()];
                for (int i = 0; i < list.size(); ++i) {
                    nArray[i] = i + 1;
                }
            }
        } else {
            nArray = new int[]{0};
        }
        return nArray;
    }

    public byte[] getSampleType(IConditionValue iConditionValue) {
        byte[] byArray;
        byte by = Byte.valueOf(iConditionValue.getConditionParamValue("SampleType", "127"));
        if (by == 66) {
            byArray = new byte[10];
            for (int i = 0; i < 10; ++i) {
                byArray[i] = OutOfSample.getISVPart(i + 1);
            }
        } else if (by == 77) {
            byArray = new byte[10];
            for (int i = 0; i < 10; ++i) {
                byArray[i] = OutOfSample.getOOSPart(i + 1);
            }
        } else {
            byArray = new byte[]{by};
        }
        return byArray;
    }
}

