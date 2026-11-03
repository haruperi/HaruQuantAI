/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 */
package com.strategyquant.datalib.session;

import com.strategyquant.lib.SQTime;
import java.util.Calendar;

public class MonthlyRangeCalculator {
    public static long getSessionStartTime(long l, long l2, long l3) {
        int n = SQTime.getDayOfWeek((long)l2);
        int n2 = SQTime.getDayOfWeek((long)l3);
        long l4 = MonthlyRangeCalculator.findFirstUsableDay(l, n, n2);
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(l4);
        calendar.set(11, SQTime.getHour((long)l2));
        calendar.set(12, SQTime.getMinute((long)l2));
        calendar.set(13, 0);
        calendar.set(14, 0);
        return calendar.getTimeInMillis();
    }

    public static long getSessionEndTime(long l, long l2, long l3) {
        int n = SQTime.getDayOfWeek((long)l2);
        int n2 = SQTime.getDayOfWeek((long)l3);
        long l4 = MonthlyRangeCalculator.findLastUsableDay(l, n, n2);
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(l4);
        calendar.set(11, SQTime.getHour((long)l3));
        calendar.set(12, SQTime.getMinute((long)l3));
        calendar.set(13, 0);
        calendar.set(14, 0);
        return calendar.getTimeInMillis();
    }

    private static long findFirstUsableDay(long l, int n, int n2) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(l);
        calendar.set(5, 1);
        calendar.add(5, -1);
        int n3 = 30;
        while (true) {
            calendar.add(5, 1);
            int n4 = SQTime.getDayOfWeek((long)calendar.getTimeInMillis());
            if (MonthlyRangeCalculator.dayIsInSession(n4, n, n2) || n3 <= 0) break;
            --n3;
        }
        return calendar.getTimeInMillis();
    }

    private static long findLastUsableDay(long l, int n, int n2) {
        Calendar calendar = Calendar.getInstance();
        calendar.setTimeInMillis(l);
        calendar.set(5, 1);
        calendar.add(2, 1);
        int n3 = 30;
        while (true) {
            calendar.add(5, -1);
            int n4 = SQTime.getDayOfWeek((long)calendar.getTimeInMillis());
            if (MonthlyRangeCalculator.dayIsInSession(n4, n, n2) || n3 <= 0) break;
            --n3;
        }
        return calendar.getTimeInMillis();
    }

    private static boolean dayIsInSession(int n, int n2, int n3) {
        int[] nArray = new int[]{1, 2, 3, 4, 5, 6, 7, 1, 2, 3, 4, 5, 6, 7};
        if (n2 > n3) {
            n3 += 7;
        }
        for (int i = n2; i <= n3; ++i) {
            if (nArray[i - 1] != n) continue;
            return true;
        }
        return false;
    }
}

