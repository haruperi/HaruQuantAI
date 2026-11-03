/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.bartype.impl;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeStatus;
import com.strategyquant.datalib.bartype.TimeframeNotSupportedException;
import com.strategyquant.datalib.bartype.impl.TimeBar;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.lib.SQTime;
import java.util.Calendar;

public class FxTimeBar
extends TimeBar {
    private final long weeklyPeriod = this.getPeriodInSeconds("Weekly", false);
    private final long monthlyPeriod = this.getPeriodInSeconds("Monthly", false);
    private long curWeekStart;
    private long nextWeekStart;
    private long curMonthStart;
    private long nextMonthStart;

    public FxTimeBar(String string) throws TimeframeNotSupportedException {
        super(1, string);
    }

    @Override
    public void processTickImplementation(TickEvent tickEvent, BarTypeStatus barTypeStatus, int n) throws DataException {
        long l = tickEvent.getTime();
        long l2 = l - this.currentBarTime;
        if (this.currentBarTime > Long.MIN_VALUE && l2 < this.periodInMs) {
            long l3;
            if (this.period >= this.weeklyPeriod) {
                barTypeStatus.status = 2;
                barTypeStatus.barTime = this.currentBarTime;
                return;
            }
            long l4 = SQTime.getDateInMs((long)l);
            if (l4 == (l3 = SQTime.getDateInMs((long)this.currentBarTime))) {
                barTypeStatus.status = 2;
                barTypeStatus.barTime = this.currentBarTime;
                return;
            }
        }
        this.currentBarTime = this.getCorrectBarTime(l, barTypeStatus.convertingToHigherTF ? tickEvent.getSessionStartTime() : this.getCorrectSessionStartTime(tickEvent.getSessionStartTime()));
        barTypeStatus.status = 1;
        barTypeStatus.barTime = this.currentBarTime;
    }

    long getCorrectBarTime(long l, long l2) throws DataException {
        long l3;
        if (this.period == 0L) {
            return l;
        }
        if (this.period == this.weeklyPeriod) {
            if (l >= this.nextWeekStart) {
                this.updateWeekStartTimes(l);
            }
            return this.curWeekStart;
        }
        if (this.period == this.monthlyPeriod) {
            if (l >= this.nextMonthStart) {
                this.updateMonthStartTimes(l);
            }
            return this.curMonthStart;
        }
        long l4 = l3 = l2 == Long.MIN_VALUE ? SQTime.correctDayStart((long)l) : l2;
        if (l == l3) {
            return l3;
        }
        long l5 = this.periodInMs;
        long l6 = l3 + l5;
        long l7 = SQTime.correctDayEnd((long)l) + 1L;
        for (int i = 0; i < 100000; ++i) {
            if (l >= l3 && l < l6) {
                return Math.min(l3, l7);
            }
            l6 = (l3 += l5) + l5;
        }
        throw new DataException(4, "Cannot find correct bar time for tick: " + SQTime.toDateMinuteString((long)l) + " and session time:" + SQTime.toDateMinuteString((long)l2));
    }

    private void updateWeekStartTimes(long l) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(SQTime.correctDayStart((long)l));
        while (calendar.get(7) != 1) {
            calendar.add(7, -1);
        }
        this.curWeekStart = calendar.getTimeInMillis();
        calendar.add(5, 7);
        this.nextWeekStart = calendar.getTimeInMillis();
    }

    private void updateMonthStartTimes(long l) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(SQTime.correctDayStart((long)l));
        while (calendar.get(5) != 1) {
            calendar.add(5, -1);
        }
        this.curMonthStart = calendar.getTimeInMillis();
        calendar.add(2, 1);
        this.nextMonthStart = calendar.getTimeInMillis();
        this.periodInMs = this.nextMonthStart - this.curMonthStart;
    }

    @Override
    public BarType clone(String string) {
        try {
            return new FxTimeBar(string);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (1)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }

    @Override
    public BarType clone() {
        try {
            return new FxTimeBar(this.timeframe);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (2)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }
}

