/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.util;

import com.strategyquant.tradinglib.ResultsGroup;
import java.util.Comparator;

public class ResultComparatorByNetProfit
implements Comparator<ResultsGroup> {
    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        try {
            double d = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)10).getDouble("NetProfit");
            double d2 = resultsGroup2.portfolio().stats((byte)0, (byte)10, (byte)10).getDouble("NetProfit");
            if (d < d2) {
                return 1;
            }
            if (d > d2) {
                return -1;
            }
        }
        catch (Exception exception) {
            exception.printStackTrace();
        }
        return 0;
    }
}

