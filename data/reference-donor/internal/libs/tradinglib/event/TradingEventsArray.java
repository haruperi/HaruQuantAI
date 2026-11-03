/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.event;

import com.strategyquant.tradinglib.event.TradingEventObj;
import java.util.ArrayList;

public class TradingEventsArray {
    private ArrayList<TradingEventObj> tradingEventsArray = new ArrayList();

    public TradingEventObj getAvailableEventObject() {
        if (this.tradingEventsArray.size() > 0) {
            for (int i = 0; i < this.tradingEventsArray.size(); ++i) {
                TradingEventObj tradingEventObj = this.tradingEventsArray.get(0);
                if (!tradingEventObj.checkAndSetInUse()) continue;
                return tradingEventObj;
            }
        }
        TradingEventObj tradingEventObj = new TradingEventObj();
        tradingEventObj.checkAndSetInUse();
        this.tradingEventsArray.add(tradingEventObj);
        return tradingEventObj;
    }
}

