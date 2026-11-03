/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.dataseries;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.dataseries.DoubleListCache;
import com.strategyquant.datalib.dataseries.IDataSeriesChangeListener;
import com.strategyquant.datalib.dataseries.IDataSeriesComputer;
import com.strategyquant.datalib.dataseries.IDoubleValuesList;
import java.security.InvalidParameterException;
import java.util.Arrays;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class DataSeriesBase {
    public static final Logger Log = LoggerFactory.getLogger((String)"DataSeriesBase");
    protected static final int DEFAULT_ALLOCATION_COUNT = 10000;
    protected static final int DEFAULT_GROW = 10000;
    protected IDoubleValuesList doubleValues = null;
    protected IDataSeriesChangeListener[] onTickChangeListeners = null;
    protected IDataSeriesChangeListener[] onBarChangeListeners = null;
    protected String dataSeriesName = null;
    protected int shift = 0;
    protected IDataSeriesComputer linkedDataComputer = null;
    protected int computedUntil = -1;
    private String lineName;
    protected int allocationSize;
    protected int growStep;
    protected String lineColor;
    private ChartDef chartDef;
    private int indyStartingBar = 0;
    private boolean showInChart = true;
    private boolean showZeroValues = true;
    private String chartType;

    public DataSeriesBase() {
        this(10000, 10000, 0);
    }

    public DataSeriesBase(int n) {
        this(n, 10000, 0);
    }

    public DataSeriesBase(int n, String string) {
        this(n, 10000, 0);
        this.dataSeriesName = string;
    }

    public DataSeriesBase(int n, String string, ChartDef chartDef) {
        this(n, 10000, 0);
        this.dataSeriesName = string;
        this.chartDef = chartDef;
    }

    public DataSeriesBase(int n, int n2) {
        this(n, 10000, 0);
    }

    private DataSeriesBase(int n, int n2, int n3) {
        this.allocationSize = n;
        this.growStep = n2;
        if (n != 0) {
            this.doubleValues = DoubleListCache.get(n);
        }
    }

    public int size() {
        return this.doubleValues.size() - this.shift;
    }

    public int specialSize() {
        return this.doubleValues.size();
    }

    protected int getRealIndex(int n) throws TradingException {
        return this.size() - n - 1;
    }

    public double _getDouble(int n) throws TradingException {
        if (n >= this.size()) {
            return 0.0;
        }
        int n2 = this.getRealIndex(n);
        this.computePotentialMissingValues(n);
        return this.doubleValues.getDouble(n2);
    }

    protected void computePotentialMissingValues(int n) throws TradingException {
        int n2;
        int n3 = n2 = n > 0 ? n - 1 : n;
        if (this.hasLinkedDataComputer() && (this.computedUntil == -1 || n2 + this.shift < this.computedUntil || n2 + this.shift == 0)) {
            this.linkedDataComputer.compute(this.computedUntil, n2 + this.shift);
        }
    }

    protected void computePotentialMissingValuesOldVersion(int n) throws TradingException {
        if (this.hasLinkedDataComputer() && (this.computedUntil == -1 || n + this.shift < this.computedUntil || n + this.shift == 0)) {
            this.linkedDataComputer.compute(this.computedUntil, n + this.shift);
        }
    }

    protected boolean hasLinkedDataComputer() {
        return this.linkedDataComputer != null;
    }

    protected void _setDouble(int n, double d, boolean bl) throws TradingException {
        this._writeDoubleToOffheap(n, d);
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

    protected void _writeDoubleToOffheap(int n, double d) {
        int n2;
        if (d > -1.0E-17 && d < 1.0E-17) {
            d = 0.0;
        }
        if (n >= (n2 = this.doubleValues.size() - this.shift)) {
            return;
        }
        if (n < 0) {
            throw new InvalidParameterException("Index cannot be smaller than zero!");
        }
        int n3 = n2 - n - 1;
        this.doubleValues.setDouble(n3, d);
    }

    public void _writeDoubleToOffheapRealIndex(int n, double d) {
        this.doubleValues.setDouble(n, d);
    }

    public void addDoubleValues(int n, double d) throws TradingException {
        if (this.shift != 0) {
            // empty if block
        }
        this.doubleValues.addDoubleValues(n, d);
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

    public void addLongValues(int n, long l) throws TradingException {
        if (this.shift != 0) {
            // empty if block
        }
        this.doubleValues.addDoubleValues(n, l);
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

    protected void _addDouble(double d) throws TradingException {
        if (this.shift != 0) {
            throw new TradingException("Shift must be 0 when calling addValues() !");
        }
        this.doubleValues.addDouble(d);
        if (this.onBarChangeListeners != null) {
            this.callOnBarChangeListeners(1, this.size());
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(1, this.size());
        }
    }

    protected void _addLong(long l) throws TradingException {
        if (this.shift != 0) {
            throw new TradingException("Shift must be 0 when calling addValues() !");
        }
        this.doubleValues.addDouble(l);
        if (this.onBarChangeListeners != null) {
            this.callOnBarChangeListeners(1, this.size());
        }
        if (this.onTickChangeListeners != null) {
            this.callOnTickChangeListeners(1, this.size());
        }
    }

    public void addChangeListener(int n, IDataSeriesChangeListener iDataSeriesChangeListener) {
        if (n == 4) {
            if (this.onTickChangeListeners == null) {
                this.onTickChangeListeners = new IDataSeriesChangeListener[1];
            } else {
                IDataSeriesChangeListener[] iDataSeriesChangeListenerArray = Arrays.copyOf(this.onTickChangeListeners, this.onTickChangeListeners.length + 1);
                this.onTickChangeListeners = iDataSeriesChangeListenerArray;
            }
            this.onTickChangeListeners[this.onTickChangeListeners.length - 1] = iDataSeriesChangeListener;
        } else {
            if (this.onBarChangeListeners == null) {
                this.onBarChangeListeners = new IDataSeriesChangeListener[1];
            } else {
                IDataSeriesChangeListener[] iDataSeriesChangeListenerArray = Arrays.copyOf(this.onBarChangeListeners, this.onBarChangeListeners.length + 1);
                this.onBarChangeListeners = iDataSeriesChangeListenerArray;
            }
            this.onBarChangeListeners[this.onBarChangeListeners.length - 1] = iDataSeriesChangeListener;
        }
    }

    protected void callOnTickChangeListeners(int n, int n2) throws TradingException {
        if (this.onTickChangeListeners == null) {
            return;
        }
        for (int i = 0; i < this.onTickChangeListeners.length; ++i) {
            this.onTickChangeListeners[i].changed(n, n2);
        }
    }

    protected void callOnBarChangeListeners(int n, int n2) throws TradingException {
        if (this.onBarChangeListeners == null) {
            return;
        }
        for (int i = 0; i < this.onBarChangeListeners.length; ++i) {
            this.onBarChangeListeners[i].changed(n, n2);
        }
    }

    public void setShift(int n) {
        this.shift = n;
    }

    public int getShift() {
        return this.shift;
    }

    public void setDataComputer(IDataSeriesComputer iDataSeriesComputer) {
        this.linkedDataComputer = iDataSeriesComputer;
    }

    public void setComputedUntil(int n) {
        this.computedUntil = n;
    }

    public void updateComputedUntil(int n) {
        if (this.computedUntil != -1 && this.computedUntil < n) {
            this.computedUntil = n;
        }
    }

    public int getComputedUntilIndex() {
        return this.computedUntil;
    }

    public void setName(String string) {
        this.dataSeriesName = string;
    }

    public void setName(String string, ChartDef chartDef) {
        this.dataSeriesName = string;
        if (this.chartDef == null && chartDef != null) {
            this.chartDef = chartDef;
        }
    }

    public String getName() {
        return this.dataSeriesName;
    }

    public void callDataChangeListeners() throws TradingException {
    }

    public void destroy() {
        if (this.doubleValues != null) {
            DoubleListCache.clear(this.doubleValues);
            this.doubleValues = null;
        }
    }

    public void setLineName(String string) {
        this.lineName = string;
    }

    public String getLineName() {
        return this.lineName;
    }

    public void setColor(String string) {
        this.lineColor = string;
    }

    public String getColor() {
        return this.lineColor;
    }

    public InstrumentInfo getInstrumentInfo() {
        if (this.chartDef != null) {
            return this.chartDef.getInstrumentInfo();
        }
        return null;
    }

    public String Symbol() {
        if (this.chartDef != null) {
            return this.chartDef.getSymbol();
        }
        return null;
    }

    public int getIndyStartingBar() {
        return this.indyStartingBar;
    }

    public void setIndyStartingBar(int n) {
        this.indyStartingBar = n;
    }

    public boolean isShowInChart() {
        return this.showInChart;
    }

    public void setShowInChart(boolean bl) {
        this.showInChart = bl;
    }

    public boolean isShowZeroValues() {
        return this.showZeroValues;
    }

    public void setShowZeroValues(boolean bl) {
        this.showZeroValues = bl;
    }

    public String getChartType() {
        return this.chartType;
    }

    public void setChartType(String string) {
        this.chartType = string;
    }
}

