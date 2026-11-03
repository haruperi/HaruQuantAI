/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 */
package com.strategyquant.datalib;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.DataSeriesBase;
import com.strategyquant.lib.SQUtils;

public class DataSeries
extends DataSeriesBase {
    private int hashCode = -1;
    static final double p6 = 1000000.0;
    static final double factor2 = 1.0E-10;

    public DataSeries() {
    }

    public DataSeries(int n) {
        super(n);
    }

    public DataSeries(String string, int n) {
        super(n, string);
    }

    public DataSeries(String string, int n, ChartDef chartDef) {
        super(n, string, chartDef);
    }

    public DataSeries(int n, int n2) {
        super(n, n2);
    }

    public DataSeries(String string) {
        super(100, string);
    }

    public int chartHashCode() {
        if (this.hashCode == -1) {
            this.hashCode = this.hashCode();
        }
        return this.hashCode;
    }

    public double get(int n) throws TradingException {
        return this._getDouble(n);
    }

    public double getRounded(int n) throws TradingException {
        double d = this._getDouble(n);
        d = (d + 1.0E-10) * 1000000.0;
        double d2 = Math.round(d);
        return d2 / 1000000.0;
    }

    public double getRounded(int n, int n2) throws TradingException {
        double d = this._getDouble(n);
        return SQUtils.round((double)d, (int)n2);
    }

    public void set(int n, double d) throws TradingException {
        this._setDouble(n, d, false);
    }

    public void set(int n, double d, boolean bl) throws TradingException {
        this._setDouble(n, d, bl);
    }

    public void set(double d) throws TradingException {
        this._setDouble(0, d, false);
    }

    public void addValues(int n) throws TradingException {
        this.addDoubleValues(n, 0.0);
    }

    public void add(double d) throws TradingException {
        this._addDouble(d);
    }
}

