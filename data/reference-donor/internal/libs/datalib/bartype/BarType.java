/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.datalib.bartype;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.data.DataException;
import java.io.Serializable;

public abstract class BarType
implements Serializable {
    protected int barTimeType;
    protected final String timeframe;

    public BarType(int n, String string) {
        this.barTimeType = n;
        this.timeframe = string;
    }

    public String getTimeframe() {
        return this.timeframe;
    }

    public String toString(String string) {
        return string;
    }

    public int getBarTimeType() {
        return this.barTimeType;
    }

    public void processTick(TickEvent tickEvent, BarTypeStatus barTypeStatus, int n) throws DataException {
        this.processTickImplementation(tickEvent, barTypeStatus, n);
    }

    public abstract void processTickImplementation(TickEvent var1, BarTypeStatus var2, int var3) throws DataException;

    public abstract BarType clone(String var1);

    public abstract BarType clone();

    public abstract boolean isTickBar();

    public abstract String checkCanBeComputedFrom(String var1) throws DataException;

    public abstract String getBaseTF();

    public abstract String getTickTF();

    public abstract long estimateStartDate(int var1, long var2);

    public abstract boolean checkTimeframeIsSupported(String var1);

    public String toStr() {
        String string = "BarTypeObj: " + this.toString();
        return string;
    }

    public abstract int getPeriodInMS();
}

