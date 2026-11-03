/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.databank;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.AbstractDatabankFilter;
import com.strategyquant.tradinglib.results.FingerprintsMap;
import com.strategyquant.tradinglib.results.StrategyFingerprint;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ImproveDatabankFilter
extends AbstractDatabankFilter {
    public static final Logger Log = LoggerFactory.getLogger(ImproveDatabankFilter.class);
    private static final String LOCK_IMPROVEDATABANKFILTER = "ImproveDatabankFilter";
    private boolean dismissTooSimilarStrategies;
    private Int2ObjectOpenHashMap<FingerprintsMap> fingerprintsMaps = new Int2ObjectOpenHashMap();

    public ImproveDatabankFilter(int n, boolean bl) {
        super(n);
        this.dismissTooSimilarStrategies = bl;
    }

    private String getBaseName(String string) {
        return string.split("- Improv")[0];
    }

    private ArrayList<String> getStrategies(String string) {
        ArrayList<String> arrayList = new ArrayList<String>();
        ArrayList<String> arrayList2 = this.databank.getRecordKeys();
        for (int i = 0; i < arrayList2.size(); ++i) {
            String string2 = arrayList2.get(i);
            if (!string2.startsWith(string) || !string2.contains(" - Improv")) continue;
            arrayList.add(string2);
        }
        return arrayList;
    }

    private ArrayList<String> getStrategiesNoLock(String string) {
        ArrayList<String> arrayList = new ArrayList<String>();
        ArrayList<String> arrayList2 = this.databank.getRecordKeysNoLock();
        for (int i = 0; i < arrayList2.size(); ++i) {
            String string2 = arrayList2.get(i);
            if (!string2.startsWith(string) || !string2.contains(" - Improv")) continue;
            arrayList.add(string2);
        }
        return arrayList;
    }

    private boolean checkFingerprint(ResultsGroup resultsGroup, StrategyFingerprint strategyFingerprint, String string) {
        strategyFingerprint.fitness = resultsGroup.getFitness();
        FingerprintsMap fingerprintsMap = (FingerprintsMap)this.fingerprintsMaps.get(SQUtils.betterHashCode((String)string));
        return fingerprintsMap != null && fingerprintsMap.checkContainsExact(strategyFingerprint);
    }

    private boolean filterOutUsingFingerprint(ResultsGroup resultsGroup, StrategyFingerprint strategyFingerprint, String string) {
        strategyFingerprint.fitness = resultsGroup.getFitness();
        FingerprintsMap fingerprintsMap = (FingerprintsMap)this.fingerprintsMaps.get(SQUtils.betterHashCode((String)string));
        if (fingerprintsMap != null) {
            if (fingerprintsMap.checkContainsExact(strategyFingerprint)) {
                return true;
            }
            StrategyFingerprint strategyFingerprint2 = fingerprintsMap.findSimilarFingerprint(strategyFingerprint);
            if (strategyFingerprint2 != null) {
                try {
                    if (this.databank.contains(strategyFingerprint2.recordName)) {
                        this.databank.removeNoLockNoException(strategyFingerprint2.recordName, true, false, true, LOCK_IMPROVEDATABANKFILTER);
                        resultsGroup.mainResult().set("ReplacedWorseStrategy", 10007);
                    }
                    fingerprintsMap.remove(strategyFingerprint2.recordName);
                }
                catch (Exception exception) {
                    Log.error("Cannot remove similar, but worse record", (Throwable)exception);
                }
                this.removeWorseStrategy(strategyFingerprint2.recordName);
                this.databank.refreshGrid();
            }
        }
        return false;
    }

    public boolean getDismissTooSimilarStrategies() {
        return this.dismissTooSimilarStrategies;
    }

    protected void addFingerprint(ResultsGroup resultsGroup, String string) {
        if (!this.dismissTooSimilarStrategies) {
            return;
        }
        if (resultsGroup != null) {
            int n = SQUtils.betterHashCode((String)string);
            FingerprintsMap fingerprintsMap = (FingerprintsMap)this.fingerprintsMaps.get(n);
            if (fingerprintsMap == null) {
                fingerprintsMap = new FingerprintsMap();
                this.fingerprintsMaps.put(n, (Object)fingerprintsMap);
            }
            fingerprintsMap.add(resultsGroup.getName(), resultsGroup.getFitness(), resultsGroup.getFingerprint());
        }
    }

    @Override
    public boolean shouldAddStrategy(ResultsGroup resultsGroup, double d) {
        StrategyFingerprint strategyFingerprint;
        String string = this.getBaseName(resultsGroup.getName());
        return !this.dismissTooSimilarStrategies || (strategyFingerprint = resultsGroup.getFingerprint()) == null || !this.checkFingerprint(resultsGroup, strategyFingerprint, string);
    }

    @Override
    protected boolean addStrategy(ResultsGroup resultsGroup, double d) throws Exception {
        ArrayList<String> arrayList;
        String string = this.getBaseName(resultsGroup.getName());
        if (this.dismissTooSimilarStrategies && (arrayList = resultsGroup.getFingerprint()) != null && this.filterOutUsingFingerprint(resultsGroup, (StrategyFingerprint)((Object)arrayList), string)) {
            return false;
        }
        arrayList = this.getStrategiesNoLock(string);
        if (arrayList.size() < this.maxRecords) {
            this.databank.refreshGrid();
            if (this.dismissTooSimilarStrategies) {
                this.addFingerprint(resultsGroup, string);
            }
            return true;
        }
        int n = arrayList.size() - this.maxRecords + 1;
        if (n > 1) {
            throw new Exception(L.t((String)"This shouldn't happen! Count: %d", (Object[])new Object[]{n}));
        }
        String string2 = this.getStrategyWithWorseRank(arrayList, d);
        if (string2 == null) {
            return false;
        }
        this.databank.removeNoLock(string2, true, false, true, LOCK_IMPROVEDATABANKFILTER);
        this.removeWorseStrategy(string2);
        if (this.dismissTooSimilarStrategies) {
            this.addFingerprint(resultsGroup, string);
        }
        this.databank.refreshGrid();
        return true;
    }
}

