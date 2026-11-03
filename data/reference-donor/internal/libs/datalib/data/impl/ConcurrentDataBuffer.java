/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.data.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import java.util.concurrent.locks.StampedLock;

public class ConcurrentDataBuffer
implements IDataBuffer {
    private TickEvent[] ring;
    private int capacity;
    private long index = -1L;
    StampedLock stampedLock = new StampedLock();

    public ConcurrentDataBuffer(int n) {
        this.capacity = n;
        this.ring = new TickEvent[n];
        for (int i = 0; i < n; ++i) {
            this.ring[i] = new TickEvent();
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void put(TickEvent tickEvent) {
        long l = this.stampedLock.writeLock();
        try {
            ++this.index;
            int n = (int)(this.index % (long)this.capacity);
            this.ring[n].copyValues(tickEvent);
        }
        finally {
            this.stampedLock.unlockWrite(l);
        }
    }

    @Override
    public void printRing() {
        String string = "Index: " + this.index + " - ";
        for (int i = 0; i < this.capacity; ++i) {
            string = string + this.ring[i].getAsk() + ",";
        }
        System.out.println(string);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public long get(long l, TickEvent[] tickEventArray) {
        long l2 = this.stampedLock.tryOptimisticRead();
        long l3 = this._get(l, tickEventArray);
        if (!this.stampedLock.validate(l2)) {
            l2 = this.stampedLock.readLock();
            try {
                l3 = this._get(l, tickEventArray);
            }
            finally {
                this.stampedLock.unlockRead(l2);
            }
        }
        return l3;
    }

    private long _get(long l, TickEvent[] tickEventArray) {
        if (this.index == -1L) {
            return -1L;
        }
        if (l >= this.index) {
            return -1L;
        }
        long l2 = this.index - (long)this.capacity;
        if (l >= 0L && l > l2) {
            l2 = l;
        }
        if (++l2 < 0L) {
            l2 = 0L;
        }
        long l3 = tickEventArray.length;
        long l4 = -1L;
        int n = 0;
        for (l4 = l2; l4 <= this.index; ++l4) {
            if ((long)n == l3) {
                return l4 - 1L;
            }
            int n2 = (int)(l4 % (long)this.capacity);
            if (n < 0) {
                System.out.println("Error J < 0 = " + n);
            }
            if (n2 < 0) {
                System.out.println("Error realPos < 0 = " + n2);
                System.out.println("i=" + l4 + ", capacity=" + this.capacity + ", lastIndex=" + l + ", index=" + this.index + ", startIndex=" + l2);
            }
            tickEventArray[n].copyValues(this.ring[n2]);
            tickEventArray[n].setIsSet(true);
            ++n;
        }
        if ((long)n < l3) {
            tickEventArray[n].setIsSet(false);
            return l4 - 1L;
        }
        return l4 - 1L;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public long getOne(long l, TickEvent tickEvent) {
        long l2 = this.stampedLock.tryOptimisticRead();
        long l3 = this._getOne(l, tickEvent);
        if (!this.stampedLock.validate(l2)) {
            l2 = this.stampedLock.readLock();
            try {
                l3 = this._getOne(l, tickEvent);
            }
            finally {
                this.stampedLock.unlockRead(l2);
            }
        }
        return l3;
    }

    private long _getOne(long l, TickEvent tickEvent) {
        if (this.index == -1L) {
            return -1L;
        }
        if (l >= this.index) {
            return -1L;
        }
        long l2 = this.index - (long)this.capacity;
        if (l >= 0L && l > l2) {
            l2 = l;
        }
        if (++l2 < 0L) {
            l2 = 0L;
        }
        boolean bl = false;
        int n = (int)(l2 % (long)this.capacity);
        tickEvent.copyValues(this.ring[n]);
        tickEvent.setIsSet(true);
        return l2;
    }
}

