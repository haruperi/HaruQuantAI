/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.util;

import com.strategyquant.tradinglib.ResultsGroup;
import java.util.Comparator;

public class ResultComparatorByName
implements Comparator<ResultsGroup> {
    @Override
    public int compare(ResultsGroup resultsGroup, ResultsGroup resultsGroup2) {
        return resultsGroup.getName().compareTo(resultsGroup2.getName());
    }
}

