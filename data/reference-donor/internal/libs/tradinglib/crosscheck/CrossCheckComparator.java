/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.crosscheck;

import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import java.util.Comparator;

public class CrossCheckComparator
implements Comparator<ICrossCheck> {
    @Override
    public int compare(ICrossCheck iCrossCheck, ICrossCheck iCrossCheck2) {
        int n = iCrossCheck.getType() - iCrossCheck2.getType();
        if (n == 0) {
            return iCrossCheck.getPreferredPosition() - iCrossCheck2.getPreferredPosition();
        }
        return n;
    }
}

