/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.results.stats.type;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.results.stats.type.IStatsType;
import java.io.Serializable;

public class StatsTypeDirection
implements IStatsType,
Serializable {
    private final byte[] keys = new byte[]{0, 1, -1};

    @Override
    public Order filterTrades(byte by, Order order, SettingsMap settingsMap) throws Exception {
        if (by == 0) {
            return order;
        }
        if (by == 1) {
            if (OrderTypes.isLongOrder(order.Type)) {
                return order;
            }
            return null;
        }
        if (by == -1) {
            if (OrderTypes.isShortOrder(order.Type)) {
                return order;
            }
            return null;
        }
        throw new Exception("Unknown key '" + by + "' in trade filter!");
    }

    @Override
    public byte[] getKeys() {
        return this.keys;
    }
}

