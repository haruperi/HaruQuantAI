/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;

public class SimpleDataBuffer
implements IDataBuffer {
    private TickEvent oneEvent = new TickEvent();
    private long index = -1L;

    @Override
    public void put(TickEvent tickEvent) {
        ++this.index;
        this.oneEvent.copyValues(tickEvent);
    }

    @Override
    public void printRing() {
        String string = "Index: " + this.index + " - ";
        string = string + this.oneEvent.getAsk() + ",";
        System.out.println(string);
    }

    @Override
    public long get(long l, TickEvent[] tickEventArray) {
        if (this.index == -1L) {
            return -1L;
        }
        if (l >= this.index) {
            return -1L;
        }
        tickEventArray[0].copyValues(this.oneEvent);
        tickEventArray[0].setIsSet(true);
        return l + 1L;
    }

    @Override
    public long getOne(long l, TickEvent tickEvent) {
        if (this.index == -1L) {
            return -1L;
        }
        if (l >= this.index) {
            return -1L;
        }
        tickEvent.copyValues(this.oneEvent);
        tickEvent.setIsSet(true);
        return l + 1L;
    }
}

