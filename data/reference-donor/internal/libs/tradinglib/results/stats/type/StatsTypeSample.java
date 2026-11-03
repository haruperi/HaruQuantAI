/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.results.stats.type;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.results.stats.type.IStatsType;
import java.io.Serializable;

public class StatsTypeSample
implements IStatsType,
Serializable {
    private final byte[] keys = new byte[]{127};

    @Override
    public Order filterTrades(byte by, Order order, SettingsMap settingsMap) throws Exception {
        return order;
    }

    @Override
    public byte[] getKeys() {
        return this.keys;
    }
}

