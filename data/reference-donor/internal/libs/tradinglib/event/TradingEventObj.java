/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.event;

import com.strategyquant.tradinglib.ILiveOrder;
import com.strategyquant.tradinglib.event.ITradingEvent;

public class TradingEventObj
implements ITradingEvent {
    private int eventType;
    private ILiveOrder order;
    private boolean inUse;

    public void setEventType(int n) {
        this.eventType = n;
    }

    public void setOrder(ILiveOrder iLiveOrder) {
        this.order = iLiveOrder;
    }

    public synchronized void releaseEvent() {
        this.inUse = false;
    }

    @Override
    public synchronized boolean checkAndSetInUse() {
        if (this.inUse) {
            return false;
        }
        this.inUse = true;
        return true;
    }
}

