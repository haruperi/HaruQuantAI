/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.time.SQTimeOld
 */
package com.strategyquant.datalib.session;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.time.SQTimeOld;
import java.io.Serializable;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Date;

public class SessionElement
implements Serializable {
    private int dayFrom;
    private int timeFrom;
    private int dayTo;
    private int timeTo;
    private int hourFrom;
    private int minuteFrom;
    private boolean eod;
    private int hourTo;
    private int minuteTo;
    private long computedRangeFrom;
    private long computedRangeTo;

    public SessionElement(int n, int n2, int n3, int n4, boolean bl) {
        if (n == n3 && n4 == 0) {
            ++n3;
        }
        n3 = n3 > 7 ? 1 : n3;
        this.dayFrom = n;
        this.timeFrom = n2;
        this.dayTo = n3;
        this.timeTo = n4;
        this.eod = bl;
        this.computedRangeFrom = -1L;
        this.computedRangeTo = -1L;
        this.hourFrom = n2 / 100;
        this.minuteFrom = n2 % 100;
        this.hourTo = n4 / 100;
        this.minuteTo = n4 % 100;
    }

    public SessionElement(String string, String string2, String string3, String string4, boolean bl) throws Exception {
        this(SessionElement.getDayInt(string), SessionElement.getTimeInt(string2), SessionElement.getDayInt(string3), SessionElement.getTimeInt(string4), bl);
    }

    public int getDayFrom() {
        return this.dayFrom;
    }

    public String getDayFromStr() throws Exception {
        return SessionElement.getDayStr(this.dayFrom);
    }

    public int getDayTo() {
        return this.dayTo;
    }

    public String getDayToStr() throws Exception {
        return SessionElement.getDayStr(this.dayTo);
    }

    public int getTimeFrom() {
        return this.timeFrom;
    }

    public String getTimeFromStr() {
        return SessionElement.getTimeStr(this.timeFrom);
    }

    public int getTimeTo() {
        return this.timeTo;
    }

    public String getTimeToStr() {
        return SessionElement.getTimeStr(this.timeTo);
    }

    public boolean isEOD() {
        return this.eod;
    }

    public void setEod(boolean bl) {
        this.eod = bl;
    }

    public boolean includesDay(int n) {
        if (this.dayFrom <= n && n <= this.dayTo) {
            return true;
        }
        if (this.dayFrom > this.dayTo) {
            if (this.dayFrom <= n) {
                return true;
            }
            if (n <= this.dayTo) {
                return true;
            }
        }
        return false;
    }

    public boolean includesTime(long l) {
        if (this.computedRangeTo == -1L || l > this.computedRangeTo) {
            this.computeRangesForNextPeriod(l);
        }
        return this.computedRangeFrom <= l && l <= this.computedRangeTo;
    }

    private void computeRangesForNextPeriod(long l) {
        int n;
        int n2 = SQTime.getDayOfWeek((long)l);
        int n3 = this.dayFrom - n2;
        if (n3 > (n = this.dayTo - n2)) {
            n3 -= 7;
        }
        if (n3 < 0 && n < 0) {
            n3 += 7;
            n += 7;
        }
        int n4 = 1900 + SQTime.getYear((long)l);
        int n5 = SQTime.getMonth((long)l) + 1;
        int n6 = SQTime.getDay((long)l);
        boolean bl = this.hourTo == 0 && this.minuteTo == 0;
        this.computedRangeFrom = SQTime.addDays((long)SQTime.toLong((int)n4, (int)n5, (int)n6, (int)this.hourFrom, (int)this.minuteFrom, (int)0), (int)n3);
        this.computedRangeTo = SQTime.addDays((long)SQTime.toLong((int)n4, (int)n5, (int)n6, (int)this.hourTo, (int)this.minuteTo, (int)0), (int)(n + (bl ? 1 : 0)));
    }

    public long getStartTime() {
        return this.computedRangeFrom;
    }

    public long getEndTime() {
        return this.computedRangeTo;
    }

    public void clearSessionTempData() {
        this.computedRangeFrom = -1L;
        this.computedRangeTo = -1L;
    }

    private static int getDayInt(String string) throws Exception {
        switch (string) {
            case "Mon": {
                return 1;
            }
            case "Tue": {
                return 2;
            }
            case "Wed": {
                return 3;
            }
            case "Thu": {
                return 4;
            }
            case "Fri": {
                return 5;
            }
            case "Sat": {
                return 6;
            }
            case "Sun": {
                return 7;
            }
        }
        throw new Exception("Day '" + string + "' not recognized");
    }

    public static int getTimeInt(String string) throws ParseException {
        SimpleDateFormat simpleDateFormat = new SimpleDateFormat("HH:mm");
        Date date = simpleDateFormat.parse(string);
        SQTimeOld sQTimeOld = new SQTimeOld(date);
        return sQTimeOld.getTimeAsTSTime();
    }

    private static String getDayStr(int n) throws Exception {
        switch (n) {
            case 1: {
                return "Mon";
            }
            case 2: {
                return "Tue";
            }
            case 3: {
                return "Wed";
            }
            case 4: {
                return "Thu";
            }
            case 5: {
                return "Fri";
            }
            case 6: {
                return "Sat";
            }
            case 7: {
                return "Sun";
            }
        }
        throw new Exception("Day '" + n + "' not recognized");
    }

    private static String getTimeStr(int n) {
        int n2 = n / 100;
        int n3 = n - n2 * 100;
        long l = SQTime.setHour((long)0L, (int)n2);
        l = SQTime.setMinute((long)l, (int)n3);
        return SQTime.formatTime((long)l);
    }

    public SessionElement clone() {
        return new SessionElement(this.dayFrom, this.timeFrom, this.dayTo, this.timeTo, this.eod);
    }

    public void fixD1DataTime(VersatileData versatileData) {
        versatileData.time = this.computedRangeTo;
    }

    public void fixD1DataTime(TickEvent tickEvent) {
        tickEvent.setTime(this.computedRangeTo);
    }
}

