/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.IProgressListener;

public interface IDatabankFilter {
    public void init(Databank var1) throws Exception;

    public void init(Databank var1, IProgressListener var2) throws Exception;

    public void destroy();

    public int getMaxStrategies();

    public double getWorstFitness();

    public boolean changeMaxRecords(int var1, IProgressListener var2) throws Exception;

    public void onRemove(String var1);

    public boolean onAdd(ResultsGroup var1);

    public void onUpdate(ResultsGroup var1);

    public boolean checkShouldAdd(ResultsGroup var1);
}

