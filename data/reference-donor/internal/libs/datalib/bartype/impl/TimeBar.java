/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.bartype.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.bartype.TimeframeNotSupportedException;
import com.strategyquant.datalib.data.DataException;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TimeBar
extends BarType {
    public static final Logger Log = LoggerFactory.getLogger((String)"TimeBar");
    protected final long period;
    protected long periodInMs;
    protected int basePeriodInMs;
    protected long currentBarTime = Long.MIN_VALUE;

    public TimeBar(String string) throws TimeframeNotSupportedException {
        super(2, string);
        this.period = this.getPeriodInSeconds(string, true);
        this.periodInMs = this.period * 1000L;
    }

    TimeBar(int n, String string) throws TimeframeNotSupportedException {
        super(n, string);
        this.period = this.getPeriodInSeconds(string, true);
        this.periodInMs = this.period * 1000L;
    }

    public long getPeriodInSeconds(String string, boolean bl) throws TimeframeNotSupportedException {
        if (string.equals("TICK")) {
            return 0L;
        }
        if (string.equals("Weekly")) {
            return 604800L;
        }
        if (string.equals("Monthly")) {
            return 2419200L;
        }
        String string2 = string.substring(0, 1);
        String string3 = string.substring(1, string.length());
        if (!(string2.equals("S") || string2.equals("M") || string2.equals("H") || string2.equals("D"))) {
            throw new TimeframeNotSupportedException("Timeframe '" + string + "' is not supported by this Bar Type!");
        }
        try {
            long l = Integer.parseInt(string3);
            if (string2.equals("S")) {
                if (bl) {
                    this.basePeriodInMs = 1000;
                }
                return l;
            }
            if (string2.equals("M")) {
                if (bl) {
                    this.basePeriodInMs = 60000;
                }
                return l * 60L;
            }
            if (string2.equals("H")) {
                if (bl) {
                    this.basePeriodInMs = 3600000;
                }
                return l * 3600L;
            }
            if (string2.equals("D")) {
                if (bl) {
                    this.basePeriodInMs = 86400000;
                }
                return l * 86400L;
            }
            throw new TimeframeNotSupportedException("Timeframe '" + string + "' is not supported by this Bar Type!");
        }
        catch (NumberFormatException numberFormatException) {
            throw new TimeframeNotSupportedException("Timeframe '" + string + "' is not supported by this Bar Type!");
        }
    }

    @Override
    public void processTickImplementation(TickEvent tickEvent, BarTypeStatus barTypeStatus, int n) throws DataException {
        long l;
        barTypeStatus.barTime = l = tickEvent.getTime();
        barTypeStatus.status = tickEvent.isBarOpen() ? 1 : 2;
    }

    @Override
    public BarType clone(String string) {
        try {
            return new TimeBar(string);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (1)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }

    @Override
    public BarType clone() {
        try {
            return new TimeBar(this.timeframe);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (2)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }

    @Override
    public boolean isTickBar() {
        return this.period == 0L;
    }

    @Override
    public String checkCanBeComputedFrom(String string) throws DataException {
        if (this.timeframe.equals(string)) {
            return null;
        }
        BarType barType = BarTypeFactory.getBarType(string, this.getBarTimeType());
        if (barType.isTickBar()) {
            return null;
        }
        if (!(barType instanceof TimeBar)) {
            return null;
        }
        TimeBar timeBar = (TimeBar)barType;
        long l = timeBar.getPeriod();
        if (this.period < l || this.period % l > 0L && this.period % 86400L > 0L) {
            return "Timeframe '" + this.toString(this.timeframe) + "' cannot be computed from timeframe '" + barType.toString(string) + "' of the stored data !";
        }
        return null;
    }

    public long getPeriod() {
        return this.period;
    }

    @Override
    public String getBaseTF() {
        return "M1";
    }

    @Override
    public String getTickTF() {
        return "TICK";
    }

    @Override
    public long estimateStartDate(int n, long l) {
        if (this.period == 0L) {
            return 0L;
        }
        return l - (long)n * (this.period * 1000L);
    }

    @Override
    public boolean checkTimeframeIsSupported(String string) {
        if ((string = string.toUpperCase()).equals("TICK")) {
            return true;
        }
        if (string.equals("Weekly".toUpperCase())) {
            return true;
        }
        if (string.equals("Monthly".toUpperCase())) {
            return true;
        }
        String string2 = string.substring(0, 1);
        String string3 = string.substring(1, string.length());
        if (!(string2.equals("S") || string2.equals("M") || string2.equals("H") || string2.equals("D"))) {
            return false;
        }
        try {
            int n = Integer.parseInt(string3);
        }
        catch (NumberFormatException numberFormatException) {
            return false;
        }
        return true;
    }

    protected long getCorrectSessionStartTime(long l) {
        if (l == Long.MIN_VALUE) {
            return l;
        }
        long l2 = this.periodInMs;
        return this.periodInMs > 0L ? l / l2 * l2 : l;
    }

    @Override
    public int getPeriodInMS() {
        return this.basePeriodInMs;
    }
}

