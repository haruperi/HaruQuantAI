/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap
 */
package com.strategyquant.tradinglib.talib;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.app.MainApp;
import it.unimi.dsi.fastutil.longs.Long2ObjectOpenHashMap;

public class TALibIndicatorsCache {
    private Long2ObjectOpenHashMap<float[][]> cache = new Long2ObjectOpenHashMap(10);
    private Long2ObjectOpenHashMap<Object[]> hashToIdentMap = new Long2ObjectOpenHashMap();

    public boolean containsKey(long l) {
        return this.cache.containsKey(l);
    }

    public long getHash(String string, String string2, SettingsMap settingsMap) {
        int n = SQUtils.betterHashCode((String)string);
        n += SQUtils.betterHashCode((String)string2);
        return n += System.identityHashCode(settingsMap);
    }

    public float[][] get(long l) {
        return (float[][])this.cache.get(l);
    }

    public void put(String string, String string2, long l, float[][] fArray, int n, int n2, String string3, SettingsMap settingsMap) {
        this.cache.put(l, (Object)fArray);
        if (!MainApp.isBacktestNode()) {
            this.hashToIdentMap.put(l, (Object)new Object[]{string, string2, n, n2, string3, l, settingsMap});
        }
    }

    public Long2ObjectOpenHashMap<Object[]> getIndicatorHashes() {
        return this.hashToIdentMap;
    }

    public void clear() {
        this.cache.clear();
        this.hashToIdentMap.clear();
    }
}

