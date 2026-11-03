/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.IDataSeriesChangeListener;
import com.strategyquant.datalib.dataseries.TimeDataSeries;

public class PreparedTimeDataSeries
extends TimeDataSeries {
    private int currentRealIndex = -1;
    private long currentValue;

    public PreparedTimeDataSeries(TimeDataSeries timeDataSeries, int n) {
        super(0);
        this.longValues = timeDataSeries.longValues;
        this.dataSeriesName = timeDataSeries.dataSeriesName;
        this.setIndyStartingBar(n);
    }

    @Override
    public void addChangeListener(int n, IDataSeriesChangeListener iDataSeriesChangeListener) {
        super.addChangeListener(n, iDataSeriesChangeListener);
    }

    @Override
    public long get(int n) throws TradingException {
        if (this.getRealIndex(n) == this.currentRealIndex) {
            return this.currentValue;
        }
        return super._getLong(n);
    }

    @Override
    public void set(int n, long l) throws TradingException {
        this.set(n, l, false);
    }

    public void set(int n, long l, boolean bl) throws TradingException {
        int n2 = this.getRealIndex(n);
        int n3 = this.getShift();
        this.currentRealIndex = n2;
        this.currentValue = l;
        if (this.hasLinkedDataComputer() && (this.computedUntil == n + n3 + 1 || this.computedUntil == -1 && n == this.size() - 1)) {
            this.computedUntil = n;
        }
        if (this.onBarChangeListeners != null && !bl) {
            this.callOnBarChangeListeners(n + n3, this.size() + n3);
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(n + n3, this.size() + n3);
        }
    }

    public void set(long l) throws TradingException {
        this.set(0, l, false);
    }

    @Override
    public void addValues(int n) throws TradingException {
        throw new TradingException("Not implemented here!");
    }

    @Override
    public void add(long l) throws TradingException {
        throw new TradingException("Not implemented here!");
    }

    public void addValuesBefore(int n) throws Exception {
        throw new TradingException("Not implemented here!");
    }

    public void addValuesBefore(int n, long l) throws Exception {
        throw new TradingException("Not implemented here!");
    }

    @Override
    public void destroy() {
    }
}

