/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.IDataSeriesChangeListener;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PreparedDataSeries
extends DataSeries {
    public static final Logger Log = LoggerFactory.getLogger((String)"Indicator");
    private int currentRealIndex = -1;
    private double currentValue;

    public PreparedDataSeries(DataSeries dataSeries, int n) {
        super(0);
        this.doubleValues = dataSeries.doubleValues;
        this.dataSeriesName = dataSeries.dataSeriesName;
        if (n > 0) {
            this.setIndyStartingBar(n);
        } else {
            this.setIndyStartingBar(dataSeries.getIndyStartingBar());
        }
    }

    @Override
    public void addChangeListener(int n, IDataSeriesChangeListener iDataSeriesChangeListener) {
        super.addChangeListener(n, iDataSeriesChangeListener);
    }

    @Override
    public double get(int n) throws TradingException {
        if (this.getRealIndex(n) == this.currentRealIndex) {
            return this.currentValue;
        }
        return super._getDouble(n);
    }

    @Override
    public void set(int n, double d) throws TradingException {
        this.set(n, d, false);
    }

    @Override
    public void set(int n, double d, boolean bl) throws TradingException {
        int n2;
        this.currentRealIndex = n2 = this.getRealIndex(n);
        this.currentValue = d;
        if (this.hasLinkedDataComputer() && (this.computedUntil == n + this.shift + 1 || this.computedUntil == -1 && n == this.size() - 1)) {
            this.computedUntil = n;
        }
        if (this.onBarChangeListeners != null && !bl) {
            this.callOnBarChangeListeners(n + this.shift, this.size() + this.shift);
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(n + this.shift, this.size() + this.shift);
        }
    }

    @Override
    protected void computePotentialMissingValues(int n) throws TradingException {
        if (this.hasLinkedDataComputer() && (this.computedUntil == -1 || n + this.shift <= this.computedUntil || n + this.shift == 0)) {
            this.linkedDataComputer.compute(this.computedUntil, n + this.shift);
        }
    }

    @Override
    public void set(double d) throws TradingException {
        this.set(0, d, false);
    }

    @Override
    public void callDataChangeListeners() throws TradingException {
        int n;
        int n2;
        if (this.onBarChangeListeners != null) {
            n2 = this.shift + 1;
            n = this.size() + this.shift;
            this.callOnBarChangeListeners(n2, n);
        }
        if (this.onTickChangeListeners != null) {
            n2 = this.shift + 1;
            n = this.size() + this.shift;
            this.callOnTickChangeListeners(n2, n);
        }
    }

    @Override
    public void addValues(int n) throws TradingException {
        throw new TradingException("Not implemented here!");
    }

    @Override
    public void add(double d) throws TradingException {
        throw new TradingException("Not implemented here!");
    }

    public void addValuesBefore(int n) throws Exception {
        throw new TradingException("Not implemented here!");
    }

    public void addValuesBefore(int n, double d) throws Exception {
        throw new TradingException("Not implemented here!");
    }

    @Override
    public void destroy() {
    }
}

