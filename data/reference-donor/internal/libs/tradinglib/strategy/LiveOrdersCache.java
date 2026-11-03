/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.InstrumentInfo
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.strategy.LiveOrderObj;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LiveOrdersCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"LiveOrdersCache");
    private LiveOrderObj[] cache = new LiveOrderObj[6];

    public LiveOrderObj createLiveOrder(Trader trader, InstrumentInfo instrumentInfo, byte by, String string) {
        LiveOrderObj liveOrderObj = this.findInCache();
        if (liveOrderObj != null) {
            liveOrderObj.init(trader, instrumentInfo, by, string);
            return liveOrderObj;
        }
        return new LiveOrderObj(trader, instrumentInfo, by, string);
    }

    public LiveOrderObj createLiveOrder(Trader trader, InstrumentInfo instrumentInfo, byte by, String string, double d) {
        LiveOrderObj liveOrderObj = this.findInCache();
        if (liveOrderObj != null) {
            liveOrderObj.init(trader, instrumentInfo, by, string, d);
            return liveOrderObj;
        }
        return new LiveOrderObj(trader, instrumentInfo, by, string, d);
    }

    private LiveOrderObj findInCache() {
        for (int i = 0; i < this.cache.length; ++i) {
            if (this.cache[i] == null) continue;
            LiveOrderObj liveOrderObj = this.cache[i];
            this.cache[i] = null;
            return liveOrderObj;
        }
        return null;
    }

    public void returnObject(LiveOrderObj liveOrderObj) {
        if (liveOrderObj == null) {
            return;
        }
        for (int i = 0; i < this.cache.length; ++i) {
            if (this.cache[i] != null) continue;
            this.cache[i] = liveOrderObj;
            return;
        }
    }
}

