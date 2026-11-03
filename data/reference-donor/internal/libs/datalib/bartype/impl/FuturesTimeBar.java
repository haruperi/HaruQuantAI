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
import com.strategyquant.datalib.session.MonthlyRangeCalculator;
import com.strategyquant.lib.SQTime;
import java.util.Calendar;

public class FuturesTimeBar
extends TimeBar {
    private final long dayPeriod = this.getPeriodInSeconds("D1", false);
    private final long weeklyPeriod = this.getPeriodInSeconds("Weekly", false);
    private final long monthlyPeriod = this.getPeriodInSeconds("Monthly", false);
    private long curWeekEnd;
    private long nextWeekEnd;
    private long curMonthEnd;
    private long nextMonthEnd;
    public boolean MetaTraderEngineUsed = false;
    public boolean LoadAsIs = false;

    public FuturesTimeBar(String string) throws TimeframeNotSupportedException {
        super(2, string);
    }

    @Override
    public void processTickImplementation(TickEvent tickEvent, BarTypeStatus barTypeStatus, int n) throws DataException {
        long l = tickEvent.getTime();
        if (this.currentBarTime > Long.MIN_VALUE && l <= this.currentBarTime) {
            barTypeStatus.status = 2;
            barTypeStatus.barTime = this.currentBarTime;
            return;
        }
        if (this.LoadAsIs) {
            barTypeStatus.convertingToHigherTF = false;
        } else if (n > 0 || this.MetaTraderEngineUsed) {
            barTypeStatus.convertingToHigherTF = true;
        }
        if (!barTypeStatus.convertingToHigherTF && l != this.currentBarTime) {
            barTypeStatus.status = 1;
            barTypeStatus.barTime = l;
            this.currentBarTime = l;
            return;
        }
        if (l == tickEvent.getSessionStartTime() && this.period != this.weeklyPeriod && this.period != this.monthlyPeriod) {
            barTypeStatus.status = 0;
            return;
        }
        this.currentBarTime = this.getCorrectBarTime(l, barTypeStatus.convertingToHigherTF ? tickEvent.getSessionStartTime() : this.getCorrectSessionStartTime(tickEvent.getSessionStartTime()), tickEvent.getSessionEndTime());
        barTypeStatus.status = 1;
        barTypeStatus.barTime = this.currentBarTime;
    }

    long getCorrectBarTime(long l, long l2, long l3) throws DataException {
        int n;
        if (this.period == 0L) {
            return l;
        }
        if (this.period == this.weeklyPeriod) {
            if (l >= this.curWeekEnd) {
                this.updateWeekStartTimes(l, l2, l3);
            }
            return this.curWeekEnd;
        }
        if (this.period == this.monthlyPeriod) {
            if (l >= this.curMonthEnd) {
                this.updateMonthStartTimes(l, l2, l3);
            }
            return this.curMonthEnd;
        }
        int n2 = SQTime.getDayOfWeek((long)l2);
        if (n2 == (n = SQTime.getDayOfWeek((long)l3)) && this.period <= this.dayPeriod) {
            return this.getCorrectBarTimeStandard(l, l2, l3);
        }
        return this.getCorrectBarTimeMultiday(l, l2, l3);
    }

    private long getCorrectBarTimeStandard(long l, long l2, long l3) throws DataException {
        long l4;
        long l5 = this.periodInMs;
        long l6 = l3 != Long.MIN_VALUE ? l3 : SQTime.correctDayEnd((long)l);
        long l7 = l4 = SQTime.correctDayStart((long)l);
        if (l2 != Long.MIN_VALUE) {
            l7 = l2 - l2 % (long)this.basePeriodInMs;
        }
        long l8 = l7 + l5;
        if (l == l7 && l2 == Long.MIN_VALUE) {
            if (this.period < this.dayPeriod) {
                return l7;
            }
            if (this.period == this.dayPeriod) {
                return l6;
            }
            return this.period < this.dayPeriod ? l8 : l7;
        }
        for (int i = 0; i < 100000; ++i) {
            if (l > l7 && l <= l8) {
                return Math.min(l8, l6);
            }
            l7 += l5;
            l8 += l5;
        }
        throw new DataException(4, "Cannot find correct bar time for tick: " + SQTime.toDateMinuteString((long)l) + " and session time:" + SQTime.toDateMinuteString((long)l2));
    }

    private long getCorrectBarTimeMultiday(long l, long l2, long l3) throws DataException {
        long l4;
        long l5;
        long l6 = this.periodInMs;
        long l7 = l3 != Long.MIN_VALUE ? l3 : SQTime.correctDayEnd((long)l) + 1L;
        long l8 = l5 = SQTime.correctDayStart((long)l);
        if (l2 != Long.MIN_VALUE) {
            l8 = l2;
        }
        if (l <= (l4 = l8 + l6)) {
            return l4;
        }
        if (l == l8) {
            return this.period < this.dayPeriod ? l4 : l8;
        }
        for (int i = 0; i < 100000; ++i) {
            if (l > l8 && l <= l4) {
                return Math.min(l4, l7);
            }
            l8 += l6;
            l4 += l6;
        }
        throw new DataException(4, "Cannot find correct bar time for tick: " + SQTime.toDateMinuteString((long)l) + " and session time:" + SQTime.toDateMinuteString((long)l2));
    }

    private void updateWeekStartTimes(long l, long l2, long l3) {
        if (l2 != Long.MIN_VALUE && l3 != Long.MIN_VALUE) {
            this.curWeekEnd = l3;
            Calendar calendar = Calendar.getInstance();
            calendar.setTimeInMillis(l3);
            calendar.add(5, 7);
            this.nextWeekEnd = calendar.getTimeInMillis();
        } else {
            Calendar calendar = Calendar.getInstance();
            calendar.setTimeInMillis(SQTime.correctDayStart((long)l));
            calendar.add(7, 1);
            while (calendar.get(7) != 1) {
                calendar.add(7, 1);
            }
            this.curWeekEnd = calendar.getTimeInMillis();
            calendar.add(5, 7);
            this.nextWeekEnd = calendar.getTimeInMillis();
        }
    }

    private void updateMonthStartTimes(long l, long l2, long l3) {
        if (l2 != Long.MIN_VALUE && l3 != Long.MIN_VALUE) {
            Calendar calendar = Calendar.getInstance();
            calendar.setTimeInMillis(l);
            calendar.set(5, 1);
            long l4 = calendar.getTimeInMillis();
            this.curMonthEnd = MonthlyRangeCalculator.getSessionEndTime(l4, l2, l3);
            calendar.setTimeInMillis(l4);
            calendar.add(2, 1);
            this.nextMonthEnd = MonthlyRangeCalculator.getSessionEndTime(calendar.getTimeInMillis(), l2, l3);
        } else {
            Calendar calendar = Calendar.getInstance();
            calendar.setTimeInMillis(SQTime.correctDayStart((long)l));
            calendar.add(5, 1);
            while (calendar.get(5) != 1) {
                calendar.add(5, 1);
            }
            this.curMonthEnd = calendar.getTimeInMillis();
            calendar.add(2, 1);
            this.nextMonthEnd = calendar.getTimeInMillis();
        }
        this.periodInMs = this.nextMonthEnd - this.curMonthEnd;
    }

    @Override
    public BarType clone(String string) {
        try {
            return new FuturesTimeBar(string);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (1)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }

    @Override
    public BarType clone() {
        try {
            return new FuturesTimeBar(this.timeframe);
        }
        catch (TimeframeNotSupportedException timeframeNotSupportedException) {
            Log.error("Exception during clone - it should never happen (2)", (Throwable)timeframeNotSupportedException);
            return null;
        }
    }
}

