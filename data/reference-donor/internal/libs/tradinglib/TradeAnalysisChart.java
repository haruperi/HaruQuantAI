/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.AbstractChart;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.TimeDuration;
import com.strategyquant.tradinglib.TimeDurationDay;
import com.strategyquant.tradinglib.TimeDurationHour;
import com.strategyquant.tradinglib.TimeDurationMin;
import com.strategyquant.tradinglib.TimeDurationOther;
import com.strategyquant.tradinglib.debug.Debugger;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public abstract class TradeAnalysisChart
extends Debugger {
    public static final Logger Log = LoggerFactory.getLogger(TradeAnalysisChart.class);
    public String name = "?";

    public String toString() {
        return this.name;
    }

    public abstract AbstractChart draw(OrdersList var1, byte var2, byte var3);

    protected String monthToString(int n) {
        switch (n) {
            case 0: {
                return "Jan";
            }
            case 1: {
                return "Feb";
            }
            case 2: {
                return "Mar";
            }
            case 3: {
                return "Apr";
            }
            case 4: {
                return "May";
            }
            case 5: {
                return "Jun";
            }
            case 6: {
                return "Jul";
            }
            case 7: {
                return "Aug";
            }
            case 8: {
                return "Sep";
            }
            case 9: {
                return "Oct";
            }
            case 10: {
                return "Nov";
            }
            case 11: {
                return "Dec";
            }
        }
        return "?";
    }

    protected String dayToString(int n) {
        switch (n) {
            case 0: {
                return "Sun";
            }
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
        }
        return "?";
    }

    protected ArrayList<TimeDuration> calculateTimeDurationScale(OrdersList ordersList) {
        ArrayList<TimeDuration> arrayList = new ArrayList<TimeDuration>();
        arrayList.clear();
        int n = this.getMaxTimeInTrade(ordersList);
        if (n < 3600) {
            arrayList.add(new TimeDurationMin(1));
            arrayList.add(new TimeDurationMin(2));
            arrayList.add(new TimeDurationMin(3));
            arrayList.add(new TimeDurationMin(4));
            arrayList.add(new TimeDurationMin(6));
            arrayList.add(new TimeDurationMin(8));
            arrayList.add(new TimeDurationMin(10));
            arrayList.add(new TimeDurationMin(15));
            arrayList.add(new TimeDurationMin(20));
            arrayList.add(new TimeDurationMin(30));
            arrayList.add(new TimeDurationMin(40));
            arrayList.add(new TimeDurationMin(50));
            arrayList.add(new TimeDurationMin(55));
            arrayList.add(new TimeDurationHour(1));
        } else if (n < 86400) {
            arrayList.add(new TimeDurationMin(5));
            arrayList.add(new TimeDurationMin(10));
            arrayList.add(new TimeDurationMin(15));
            arrayList.add(new TimeDurationMin(30));
            arrayList.add(new TimeDurationHour(1));
            arrayList.add(new TimeDurationHour(2));
            arrayList.add(new TimeDurationHour(4));
            arrayList.add(new TimeDurationHour(8));
            arrayList.add(new TimeDurationHour(10));
            arrayList.add(new TimeDurationHour(12));
            arrayList.add(new TimeDurationHour(16));
            arrayList.add(new TimeDurationHour(18));
            arrayList.add(new TimeDurationHour(20));
            arrayList.add(new TimeDurationDay(1));
        } else if (n < 691200) {
            arrayList.add(new TimeDurationMin(5));
            arrayList.add(new TimeDurationMin(10));
            arrayList.add(new TimeDurationMin(15));
            arrayList.add(new TimeDurationMin(30));
            arrayList.add(new TimeDurationHour(1));
            arrayList.add(new TimeDurationHour(2));
            arrayList.add(new TimeDurationHour(4));
            arrayList.add(new TimeDurationHour(8));
            arrayList.add(new TimeDurationHour(16));
            arrayList.add(new TimeDurationHour(18));
            arrayList.add(new TimeDurationHour(22));
            arrayList.add(new TimeDurationDay(1));
            arrayList.add(new TimeDurationDay(4));
            arrayList.add(new TimeDurationDay(8));
        } else {
            arrayList.add(new TimeDurationMin(5));
            arrayList.add(new TimeDurationMin(10));
            arrayList.add(new TimeDurationMin(15));
            arrayList.add(new TimeDurationMin(30));
            arrayList.add(new TimeDurationHour(1));
            arrayList.add(new TimeDurationHour(4));
            arrayList.add(new TimeDurationHour(8));
            arrayList.add(new TimeDurationHour(16));
            arrayList.add(new TimeDurationDay(1));
            arrayList.add(new TimeDurationDay(4));
            arrayList.add(new TimeDurationDay(8));
            arrayList.add(new TimeDurationDay(16));
            arrayList.add(new TimeDurationDay(30));
            arrayList.add(new TimeDurationOther());
        }
        return arrayList;
    }

    private int getMaxTimeInTrade(OrdersList ordersList) {
        int n = -1;
        int n2 = -1;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            n2 = order.Duration;
            if (n2 <= n) continue;
            n = n2;
        }
        return n;
    }
}

