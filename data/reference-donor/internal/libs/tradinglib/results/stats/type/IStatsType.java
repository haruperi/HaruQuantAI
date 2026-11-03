/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.results.stats.type;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.Order;

public interface IStatsType {
    public Order filterTrades(byte var1, Order var2, SettingsMap var3) throws Exception;

    public byte[] getKeys();
}

