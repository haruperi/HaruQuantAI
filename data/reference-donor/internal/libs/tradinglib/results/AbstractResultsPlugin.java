/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.tradinglib.results.IResultPlugin;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;

public abstract class AbstractResultsPlugin
implements IResultPlugin {
    protected IResultsGroupProvider rgProvider;

    @Override
    public void setResultsGroupProvider(IResultsGroupProvider iResultsGroupProvider) {
        this.rgProvider = iResultsGroupProvider;
    }
}

