/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TimePeriod
 *  com.strategyquant.lib.TimePeriods
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.lib.TimePeriods;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CorrelationLib {
    public static final Logger Log = LoggerFactory.getLogger((String)"CorrelationLib");

    public static TimePeriod getPeriod(OrdersList ordersList, OrdersList ordersList2) {
        TimePeriod timePeriod = CorrelationLib.getPeriod(ordersList);
        TimePeriod timePeriod2 = CorrelationLib.getPeriod(ordersList2);
        long l = timePeriod.from < timePeriod2.from ? timePeriod.from : timePeriod2.from;
        long l2 = timePeriod.to > timePeriod2.to ? timePeriod.to : timePeriod2.to;
        timePeriod = null;
        timePeriod2 = null;
        return new TimePeriod(l, l2);
    }

    public static TimePeriod getPeriod(OrdersList ordersList) {
        long l = -1L;
        long l2 = -1L;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            if (l == -1L || l > order.OpenTime) {
                l = order.OpenTime;
            }
            if (l2 >= order.CloseTime) continue;
            l2 = order.CloseTime;
        }
        return new TimePeriod(l, l2);
    }

    public static TimePeriods generatePeriods(int n, long l, long l2) {
        long l3;
        TimePeriods timePeriods = new TimePeriods();
        long l4 = l = CorrelationLib.getCorrectPeriod(l, n);
        do {
            l3 = l4;
            l3 = CorrelationLib.increasePeriod(l3, n);
            TimePeriod timePeriod = new TimePeriod(l4, l3, CorrelationLib.printPeriod(l4, n));
            timePeriods.put(l4, (Object)timePeriod);
        } while ((l4 = l3) <= l2);
        return timePeriods;
    }

    private static long increasePeriod(long l, int n) {
        switch (n) {
            case 5: {
                return SQTime.addHours((long)l, (int)1);
            }
            case 10: {
                return SQTime.addDays((long)l, (int)1);
            }
            case 20: {
                return SQTime.addWeeks((long)l, (int)1);
            }
            case 30: {
                return SQTime.addMonths((long)l, (int)1);
            }
            case 40: {
                return SQTime.addYears((long)l, (int)1);
            }
        }
        return l;
    }

    public static String printPeriod(long l, int n) {
        if (n == 5) {
            return SQTime.toDateString((long)l) + " " + SQTime.getHour((long)l) + ":00";
        }
        if (n == 40) {
            return SQTime.getFullYear((long)l) + " year " + SQTime.getYear((long)l);
        }
        if (n == 30) {
            return SQTime.getFullYear((long)l) + " month " + SQTime.getMonthOriginal((long)l);
        }
        if (n == 20) {
            return SQTime.getFullYear((long)l) + " week " + (SQTime.getWeekOfYear((long)l) + 1);
        }
        return SQTime.toDateString((long)l);
    }

    public static long getCorrectPeriod(long l, int n) {
        long l2 = l;
        switch (n) {
            case 5: {
                l2 = SQTime.setMinute((long)l2, (int)0);
                l2 = SQTime.setSecond((long)l2, (int)0);
                l2 = SQTime.setMiliSeconds((long)l2, (int)0);
                break;
            }
            case 10: {
                l2 = SQTime.setHour((long)l2, (int)0);
                l2 = SQTime.setMinute((long)l2, (int)0);
                l2 = SQTime.setSecond((long)l2, (int)0);
                l2 = SQTime.setMiliSeconds((long)l2, (int)0);
                break;
            }
            case 20: {
                l2 = SQTime.setDayOfWeek((long)l2, (int)1);
                l2 = SQTime.setHour((long)l2, (int)0);
                l2 = SQTime.setMinute((long)l2, (int)0);
                l2 = SQTime.setSecond((long)l2, (int)0);
                l2 = SQTime.setMiliSeconds((long)l2, (int)0);
                break;
            }
            case 30: {
                l2 = SQTime.setDayOfMonth((long)l2, (int)1);
                l2 = SQTime.setHour((long)l2, (int)0);
                l2 = SQTime.setMinute((long)l2, (int)0);
                l2 = SQTime.setSecond((long)l2, (int)0);
                l2 = SQTime.setMiliSeconds((long)l2, (int)0);
                break;
            }
            case 40: {
                l2 = SQTime.setMonthOfYear((long)l2, (int)1);
                l2 = SQTime.setDayOfMonth((long)l2, (int)1);
                l2 = SQTime.setHour((long)l2, (int)0);
                l2 = SQTime.setMinute((long)l2, (int)0);
                l2 = SQTime.setSecond((long)l2, (int)0);
                l2 = SQTime.setMiliSeconds((long)l2, (int)0);
            }
        }
        return l2;
    }
}

