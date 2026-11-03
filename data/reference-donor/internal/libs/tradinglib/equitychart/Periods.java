/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TimePeriod
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.SampleTypes;
import java.util.ArrayList;
import java.util.List;

public class Periods {
    public List<TimePeriod> getAvailablePeriods(OrdersList ordersList, String string) throws Exception {
        ArrayList<TimePeriod> arrayList = new ArrayList<TimePeriod>();
        TimePeriod timePeriod = null;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            if (timePeriod != null) {
                if (timePeriod.name == SampleTypes.typeToString(order.SampleType)) {
                    timePeriod.to = this.getX(order.CloseTime, i, string);
                } else {
                    timePeriod.to = this.getX(order.OpenTime, i, string);
                    arrayList.add(timePeriod);
                    timePeriod = null;
                }
            }
            if (timePeriod != null) continue;
            timePeriod = new TimePeriod();
            timePeriod.from = this.getX(order.OpenTime, i, string);
            timePeriod.to = this.getX(order.CloseTime, i, string);
            timePeriod.name = SampleTypes.typeToString(order.SampleType);
            timePeriod.type = order.SampleType;
            timePeriod.note = order.Ticket + "";
        }
        if (timePeriod != null) {
            arrayList.add(timePeriod);
        }
        return arrayList;
    }

    private long getX(long l, int n, String string) {
        if (string.equals("time")) {
            return SQTime.getDateInMs((long)l);
        }
        return n;
    }

    public List<TimePeriod> filter(List<TimePeriod> list, byte by) {
        ArrayList<TimePeriod> arrayList = new ArrayList<TimePeriod>();
        for (int i = 0; i < list.size(); ++i) {
            TimePeriod timePeriod = list.get(i);
            if (by == 40 && SampleTypes.isISV(timePeriod.type)) {
                arrayList.add(timePeriod);
                continue;
            }
            if (by != 20 || !SampleTypes.isOOS(timePeriod.type)) continue;
            arrayList.add(timePeriod);
        }
        return arrayList;
    }
}

