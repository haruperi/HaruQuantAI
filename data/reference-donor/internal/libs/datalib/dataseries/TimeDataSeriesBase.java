/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.DataSeriesBase;
import com.strategyquant.datalib.dataseries.ILongValuesList;
import com.strategyquant.datalib.dataseries.LongListCache;

public abstract class TimeDataSeriesBase
extends DataSeriesBase {
    protected ILongValuesList longValues = null;

    public TimeDataSeriesBase() {
        this(10000, 10000, null);
    }

    public TimeDataSeriesBase(int n) {
        this(n, 10000, null);
    }

    public TimeDataSeriesBase(int n, String string) {
        this(n, 10000, string);
    }

    public TimeDataSeriesBase(int n, String string, ChartDef chartDef) {
        super(0, string, chartDef);
        this.allocationSize = n;
        this.growStep = 10000;
    }

    public TimeDataSeriesBase(int n, int n2) {
        this(n, n2, null);
    }

    public TimeDataSeriesBase(int n, int n2, String string) {
        super(0, string);
        this.allocationSize = n;
        this.growStep = n2;
    }

    protected synchronized void checkValuesInitialized() {
        if (this.longValues == null && this.allocationSize != 0) {
            this.longValues = LongListCache.get(this.allocationSize);
        }
    }

    protected long _getLong(int n) throws TradingException {
        this.checkValuesInitialized();
        if (n >= this.size()) {
            return 0L;
        }
        int n2 = this.getRealIndex(n);
        this.computePotentialMissingValues(n);
        if (n2 == this.longValues.size()) {
            return 0L;
        }
        return this.longValues.getLong(n2);
    }

    protected void _setLong(int n, long l) throws TradingException {
        this.checkValuesInitialized();
        if (n >= this.size()) {
            return;
        }
        int n2 = this.getRealIndex(n);
        this.longValues.setLong(n2, l);
        if (this.hasLinkedDataComputer() && (this.computedUntil == n + this.shift + 1 || this.computedUntil == -1 && n == this.size() - 1)) {
            this.computedUntil = n;
        }
        if (this.onBarChangeListeners != null) {
            this.callOnBarChangeListeners(n + this.shift, this.size() + this.shift);
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(n + this.shift, this.size() + this.shift);
        }
    }

    @Override
    public void addLongValues(int n, long l) throws TradingException {
        this.checkValuesInitialized();
        if (this.shift != 0) {
            // empty if block
        }
        for (int i = 0; i < n; ++i) {
            this.longValues.addLong(l);
        }
        if (this.hasLinkedDataComputer() && this.computedUntil > -1) {
            this.computedUntil += n;
        }
        if (this.onBarChangeListeners != null) {
            this.callOnBarChangeListeners(n - 1, this.size());
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(n - 1, this.size());
        }
    }

    @Override
    protected void _addLong(long l) throws TradingException {
        this.checkValuesInitialized();
        if (this.shift != 0) {
            throw new TradingException("Shift must be 0 when calling addValues() !");
        }
        this.longValues.addLong(l);
        if (this.onBarChangeListeners != null) {
            this.callOnBarChangeListeners(1, this.size());
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(1, this.size());
        }
    }

    @Override
    public void destroy() {
        if (this.longValues != null) {
            LongListCache.clear(this.longValues);
            this.longValues = null;
        }
    }

    @Override
    public int size() {
        this.checkValuesInitialized();
        return this.longValues.size() - this.shift;
    }

    @Override
    public int specialSize() {
        this.checkValuesInitialized();
        return this.longValues.size();
    }

    public long getDateBarsFromDate(long l, int n) {
        int n2 = -1;
        n2 = l == 0L ? 0 : this.getDFIndexSlow(l);
        if (n2 == -1) {
            return this.longValues.getLong(this.longValues.size() - 1);
        }
        int n3 = n2 + n;
        if (n3 < 0) {
            return this.longValues.getLong(0);
        }
        if (n3 >= this.longValues.size()) {
            return this.longValues.getLong(this.longValues.size() - 1);
        }
        return this.longValues.getLong(n3);
    }

    protected int getDFIndexEffective(long l) {
        int n;
        int n2 = -2;
        int n3 = this.longValues.size();
        if (n3 <= 0) {
            return n2;
        }
        long l2 = this.longValues.getLong(0);
        long l3 = this.longValues.getLong(n3 - 1);
        int n4 = (int)((l3 - l2) / (long)n3);
        if (n4 == 0) {
            n4 = 1;
        }
        if ((n = (int)((l - l2) / (long)(n4 = (int)((double)n4 * 1.2)))) == 0) {
            n = 1;
        }
        for (int i = n - 1; i < this.longValues.size(); ++i) {
            long l4 = this.longValues.getLong(i);
            if (l4 < l) continue;
            n2 = i;
            break;
        }
        return n2;
    }

    protected int getDFIndexSlow(long l) {
        int n = -1;
        for (int i = 0; i < this.longValues.size(); ++i) {
            long l2 = this.longValues.getLong(i);
            if (l2 < l) continue;
            n = i;
            break;
        }
        return n;
    }
}

