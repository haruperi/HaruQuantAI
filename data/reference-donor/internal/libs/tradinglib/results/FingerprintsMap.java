/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.IntOpenHashSet
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.tradinglib.results.StrategyFingerprint;
import it.unimi.dsi.fastutil.ints.IntOpenHashSet;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FingerprintsMap {
    public static final Logger Log = LoggerFactory.getLogger((String)"FingerprintsMap");
    private ObjectArrayList<StrategyFingerprint> fingerprints = new ObjectArrayList();
    private IntOpenHashSet strategyNames = new IntOpenHashSet();
    private IntOpenHashSet exactFingerprints = new IntOpenHashSet();

    public boolean checkContainsExact(StrategyFingerprint strategyFingerprint) {
        if (this.exactFingerprints.contains(strategyFingerprint.exactFingerprint)) {
            for (int i = 0; i < this.fingerprints.size(); ++i) {
                StrategyFingerprint strategyFingerprint2 = (StrategyFingerprint)this.fingerprints.get(i);
                if (strategyFingerprint.exactFingerprint != strategyFingerprint2.exactFingerprint) continue;
            }
        }
        return this.exactFingerprints.contains(strategyFingerprint.exactFingerprint);
    }

    public void add(String string, double d, StrategyFingerprint strategyFingerprint) {
        if (strategyFingerprint == null) {
            return;
        }
        this.strategyNames.add(string.hashCode());
        this.exactFingerprints.add(strategyFingerprint.exactFingerprint);
        strategyFingerprint.recordName = string;
        strategyFingerprint.fitness = d;
        this.fingerprints.add((Object)strategyFingerprint);
    }

    public void remove(String string) {
        if (!this.strategyNames.contains(string.hashCode())) {
            return;
        }
        StrategyFingerprint strategyFingerprint = this.findFingerprint(string);
        if (strategyFingerprint == null) {
            return;
        }
        this.exactFingerprints.remove(strategyFingerprint.exactFingerprint);
        this.fingerprints.remove((Object)strategyFingerprint);
    }

    private StrategyFingerprint findFingerprint(String string) {
        for (int i = 0; i < this.fingerprints.size(); ++i) {
            StrategyFingerprint strategyFingerprint = (StrategyFingerprint)this.fingerprints.get(i);
            if (!strategyFingerprint.recordName.equals(string)) continue;
            return strategyFingerprint;
        }
        return null;
    }

    public StrategyFingerprint findSimilarFingerprint(StrategyFingerprint strategyFingerprint) {
        double d;
        double d2;
        double d3 = (double)strategyFingerprint.trades * 0.05;
        int n = (int)d3;
        if (n == 0) {
            n = 1;
        }
        int n2 = strategyFingerprint.trades - n;
        int n3 = strategyFingerprint.trades + n;
        double d4 = strategyFingerprint.profit - strategyFingerprint.profit * 0.05;
        double d5 = strategyFingerprint.profit + strategyFingerprint.profit * 0.05;
        if (d4 > d5) {
            d2 = d4;
            d4 = d5;
            d5 = d2;
        }
        if ((d2 = strategyFingerprint.drawdown - strategyFingerprint.drawdown * 0.05) > (d = strategyFingerprint.drawdown + strategyFingerprint.drawdown * 0.05)) {
            double d6 = d2;
            d2 = d;
            d = d6;
        }
        int n4 = strategyFingerprint.tradesHash;
        for (int i = 0; i < this.fingerprints.size(); ++i) {
            StrategyFingerprint strategyFingerprint2 = (StrategyFingerprint)this.fingerprints.get(i);
            if (strategyFingerprint2.trades < n2 || strategyFingerprint2.trades > n3 || strategyFingerprint2.profit < d4 || strategyFingerprint2.profit > d5 || strategyFingerprint2.drawdown < d2 || strategyFingerprint2.drawdown > d || n4 != -1 && strategyFingerprint2.tradesHash != -1 && n4 != strategyFingerprint2.tradesHash || !(strategyFingerprint2.fitness < strategyFingerprint.fitness)) continue;
            return strategyFingerprint2;
        }
        return null;
    }
}

