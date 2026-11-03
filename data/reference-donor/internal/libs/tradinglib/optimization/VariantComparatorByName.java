/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.wfo.WFVariant;
import java.util.Comparator;

public class VariantComparatorByName
implements Comparator<WFVariant> {
    @Override
    public int compare(WFVariant wFVariant, WFVariant wFVariant2) {
        return wFVariant.params.compareTo(wFVariant2.params);
    }
}

