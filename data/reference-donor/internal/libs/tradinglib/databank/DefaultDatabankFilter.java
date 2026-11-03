/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.AbstractDatabankFilter;
import com.strategyquant.tradinglib.results.FingerprintsMap;
import com.strategyquant.tradinglib.results.StrategyFingerprint;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DefaultDatabankFilter
extends AbstractDatabankFilter {
    public static final Logger Log = LoggerFactory.getLogger(DefaultDatabankFilter.class);
    private static final String LOCK_DEFAULTDATABANKFILTER = "DefaultDatabankFilter";
    private boolean dismissTooSimilarStrategies;
    private FingerprintsMap fingerprintsMap = new FingerprintsMap();

    public DefaultDatabankFilter(int n, boolean bl) {
        super(n);
        this.dismissTooSimilarStrategies = bl;
    }

    private boolean filterOutUsingFingerprint(ResultsGroup resultsGroup, StrategyFingerprint strategyFingerprint) {
        strategyFingerprint.fitness = resultsGroup.getFitness();
        if (this.fingerprintsMap.checkContainsExact(strategyFingerprint)) {
            return true;
        }
        StrategyFingerprint strategyFingerprint2 = this.fingerprintsMap.findSimilarFingerprint(strategyFingerprint);
        if (strategyFingerprint2 != null) {
            try {
                if (this.databank.contains(strategyFingerprint2.recordName)) {
                    this.databank.removeNoLockNoException(strategyFingerprint2.recordName, true, false, true, LOCK_DEFAULTDATABANKFILTER);
                    resultsGroup.mainResult().set("ReplacedWorseStrategy", 10007);
                }
                this.fingerprintsMap.remove(strategyFingerprint2.recordName);
            }
            catch (Exception exception) {
                Log.error("Cannot remove similar, but worse record", (Throwable)exception);
            }
            this.removeWorseStrategy(strategyFingerprint2.recordName);
            this.databank.refreshGrid();
        }
        return false;
    }

    private boolean checkFingerprint(ResultsGroup resultsGroup, StrategyFingerprint strategyFingerprint) {
        strategyFingerprint.fitness = resultsGroup.getFitness();
        return this.fingerprintsMap.checkContainsExact(strategyFingerprint);
    }

    public boolean getDismissTooSimilarStrategies() {
        return this.dismissTooSimilarStrategies;
    }

    protected void addFingerprint(ResultsGroup resultsGroup) {
        if (!this.dismissTooSimilarStrategies) {
            return;
        }
        if (resultsGroup != null) {
            this.fingerprintsMap.add(resultsGroup.getName(), resultsGroup.getFitness(), resultsGroup.getFingerprint());
        }
    }

    protected void removeFingerprint(String string) {
        if (!this.dismissTooSimilarStrategies) {
            return;
        }
        this.fingerprintsMap.remove(string);
    }

    @Override
    public void onRemove(String string) {
        super.onRemove(string);
        if (!this.dismissTooSimilarStrategies) {
            return;
        }
        this.fingerprintsMap.remove(string);
    }

    @Override
    public boolean shouldAddStrategy(ResultsGroup resultsGroup, double d) {
        StrategyFingerprint strategyFingerprint;
        if (this.dismissTooSimilarStrategies && (strategyFingerprint = resultsGroup.getFingerprint()) != null && this.checkFingerprint(resultsGroup, strategyFingerprint)) {
            return false;
        }
        if (this.databank.getRecordsSizeNoLock() >= this.maxRecords && this.maxRecords > 0) {
            double d2 = this.getWorstRankValue();
            return d > d2;
        }
        return true;
    }

    @Override
    protected boolean addStrategy(ResultsGroup resultsGroup, double d) throws Exception {
        Object object;
        if (this.dismissTooSimilarStrategies && (object = resultsGroup.getFingerprint()) != null && this.filterOutUsingFingerprint(resultsGroup, (StrategyFingerprint)object)) {
            return false;
        }
        while (this.databank.getRecordsSizeNoLock() >= this.maxRecords && this.maxRecords > 0) {
            object = this.getWorstStrategy();
            double d2 = this.getWorstRankValue();
            if (d > d2) {
                this.databank.removeNoLockNoException((String)object, true, false, true, LOCK_DEFAULTDATABANKFILTER);
                this.removeWorseStrategy((String)object);
                resultsGroup.mainResult().set("ReplacedWorseStrategy", 10007);
                Log.debug("Strategy {} replaced by better (1)", (Object)resultsGroup.getName());
                continue;
            }
            Log.debug("Strategy{} not added, its fitness was lower than worst fitness in databank", (Object)resultsGroup.getName());
            this.databank.refreshGrid();
            return false;
        }
        if (this.dismissTooSimilarStrategies) {
            this.fingerprintsMap.add(resultsGroup.getName(), resultsGroup.getFitness(), resultsGroup.getFingerprint());
        }
        this.databank.refreshGrid();
        return true;
    }
}

