/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data;

import com.strategyquant.datalib.customData.CustomDataInfo;
import it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CustomDataIndyMap {
    private static final Logger Log = LoggerFactory.getLogger(CustomDataIndyMap.class);
    private Long2DoubleOpenHashMap map = new Long2DoubleOpenHashMap();
    private String indyId;
    private CustomDataInfo dataInfo;
    private int value;

    CustomDataIndyMap(String string, CustomDataInfo customDataInfo, int n) {
        this.indyId = string;
        this.dataInfo = customDataInfo;
        this.value = n;
    }

    public double getTime(long l) {
        return this.map.getOrDefault(l, 0.0);
    }

    public void put(long l, double d) {
        this.map.put(l, d);
    }

    public String getName() {
        return this.indyId;
    }

    public int getValueIndex() {
        return this.value;
    }
}

