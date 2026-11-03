/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.AbstractDatabankFilter;
import com.strategyquant.tradinglib.databank.IProgressListener;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizeDatabankFilter
extends AbstractDatabankFilter {
    public static final Logger Log = LoggerFactory.getLogger(OptimizeDatabankFilter.class);
    private static final String LOCK_OPTIMDATABANKFILTER = "OptimizeDatabankFilter";
    private IntOpenHashSet storedStrategies = new IntOpenHashSet();

    public OptimizeDatabankFilter(int n) {
        super(n);
    }

    @Override
    public void init(Databank databank, IProgressListener iProgressListener) throws Exception {
        this.databank = databank;
        this.calculateRankValues();
    }

    @Override
    public boolean shouldAddStrategy(ResultsGroup resultsGroup, double d) {
        String string = this.getBaseName(resultsGroup.getName());
        int n = this.computeStrategyParamsHash(string, resultsGroup);
        if (this.storedStrategies.contains(n)) {
            return false;
        }
        ArrayList<String> arrayList = this.getStrategies(string);
        if (arrayList.size() < this.maxRecords) {
            return true;
        }
        return this.hasWorseRankValue(arrayList, d);
    }

    @Override
    public boolean addStrategy(ResultsGroup resultsGroup, double d) throws Exception {
        String string = this.getBaseName(resultsGroup.getName());
        int n = this.computeStrategyParamsHash(string, resultsGroup);
        if (this.storedStrategies.contains(n)) {
            return false;
        }
        ArrayList<String> arrayList = this.getStrategiesNoLock(string);
        if (arrayList.size() < this.maxRecords) {
            this.databank.refreshGrid();
            return true;
        }
        int n2 = arrayList.size() - this.maxRecords + 1;
        if (n2 > 1) {
            boolean bl;
            boolean bl2 = bl = true;
            throw new Exception(L.t((String)"This shouldn't happen! Count: %d", (Object[])new Object[]{n2}));
        }
        String string2 = this.getStrategyWithWorseRank(arrayList, d);
        if (string2 != null) {
            this.databank.removeNoLock(string2, true, false, true, LOCK_OPTIMDATABANKFILTER);
            this.removeWorseStrategy(string2);
            this.databank.refreshGrid();
            return true;
        }
        return false;
    }

    @Override
    protected void actionOnInsert(ResultsGroup resultsGroup) {
        if (resultsGroup == null) {
            return;
        }
        String string = this.getBaseName(resultsGroup.getName());
        int n = this.computeStrategyParamsHash(string, resultsGroup);
        this.storedStrategies.add(n);
    }

    private String getBaseName(String string) {
        return string.split("- Optimiz")[0];
    }

    protected ArrayList<String> getStrategiesNoLock(String string) {
        return this.databank.getRecordKeysNoLock(string);
    }

    protected ArrayList<String> getStrategies(String string) {
        return this.databank.getRecordKeys(string);
    }

    private int computeStrategyParamsHash(String string, ResultsGroup resultsGroup) {
        StringBuffer stringBuffer = new StringBuffer(string);
        stringBuffer.append(resultsGroup.getParams());
        return stringBuffer.toString().hashCode();
    }
}

