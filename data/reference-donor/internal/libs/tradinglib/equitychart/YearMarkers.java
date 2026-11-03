/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TimePeriod
 *  it.unimi.dsi.fastutil.longs.Long2IntAVLTreeMap
 *  it.unimi.dsi.fastutil.longs.Long2IntMap$Entry
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.equitychart.AreaFill;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import it.unimi.dsi.fastutil.longs.Long2IntAVLTreeMap;
import it.unimi.dsi.fastutil.longs.Long2IntMap;
import java.awt.Color;
import java.util.ArrayList;
import java.util.Calendar;

public class YearMarkers {
    public static final Color COLOR_LIGHT_GRAY = new Color(208, 208, 208);
    private Calendar cal = Calendar.getInstance();

    public void print(EquityChart equityChart, OrdersList ordersList, String string) {
        ArrayList<TimePeriod> arrayList = this.getAvailablePeriods(ordersList, string);
        if (arrayList.isEmpty()) {
            return;
        }
        for (TimePeriod timePeriod : arrayList) {
            AreaFill areaFill = new AreaFill();
            areaFill.text = timePeriod.name;
            areaFill.borderColor = "#D0D0D0";
            areaFill.textColor = "#D0D0D0";
            areaFill.borderColorDark = "#545454";
            areaFill.textColorDark = "#aaa";
            areaFill.borderOnly = true;
            areaFill.xFrom = timePeriod.from;
            areaFill.xTo = timePeriod.to;
            areaFill.verticalAlign = "bottom";
            equityChart.addArea(areaFill);
        }
    }

    private ArrayList<TimePeriod> getAvailablePeriods(OrdersList ordersList, String string) {
        Object object;
        ArrayList<TimePeriod> arrayList = new ArrayList<TimePeriod>();
        int n = -1;
        int n2 = -1;
        if (string.equals("time")) {
            long l;
            object = new Long2IntAVLTreeMap();
            for (int i = 0; i < ordersList.size(); ++i) {
                Order order = ordersList.get(i);
                l = SQTime.getDateInMs((long)order.CloseTime);
                n = SQTime.getFullYear((long)order.CloseTime);
                object.put(l, n);
            }
            long l2 = 0L;
            for (Long2IntMap.Entry entry : object.long2IntEntrySet()) {
                TimePeriod timePeriod;
                l = entry.getLongKey();
                n = entry.getIntValue();
                if (arrayList.isEmpty()) {
                    timePeriod = new TimePeriod();
                    timePeriod.name = n + "";
                    timePeriod.from = string.equals("time") ? this.getYearInMs(l) : l2;
                    timePeriod.to = 0L;
                    arrayList.add(timePeriod);
                } else if (n2 != n) {
                    timePeriod = arrayList.get(arrayList.size() - 1);
                    timePeriod.to = string.equals("time") ? this.getYearInMs(l) : l2;
                    timePeriod = new TimePeriod();
                    timePeriod.name = n + "";
                    timePeriod.from = string.equals("time") ? this.getYearInMs(l) : l2;
                    timePeriod.to = 0L;
                    arrayList.add(timePeriod);
                }
                n2 = n;
                ++l2;
            }
        } else {
            for (int i = 0; i < ordersList.size(); ++i) {
                TimePeriod timePeriod;
                Order order = ordersList.get(i);
                long l = SQTime.getDateInMs((long)order.CloseTime);
                n = SQTime.getFullYear((long)order.CloseTime);
                if (arrayList.isEmpty()) {
                    timePeriod = new TimePeriod();
                    timePeriod.name = n + "";
                    timePeriod.from = i;
                    timePeriod.to = 0L;
                    arrayList.add(timePeriod);
                } else if (n2 != n) {
                    timePeriod = arrayList.get(arrayList.size() - 1);
                    timePeriod.to = i;
                    timePeriod = new TimePeriod();
                    timePeriod.name = n + "";
                    timePeriod.from = i;
                    timePeriod.to = 0L;
                    arrayList.add(timePeriod);
                }
                n2 = n;
            }
        }
        if (!arrayList.isEmpty() && arrayList.get((int)(arrayList.size() - 1)).to == 0L) {
            if (string.equals("time")) {
                object = EquityChartUtils.dateRange(ordersList);
                arrayList.get((int)(arrayList.size() - 1)).to = (long)object[1];
            } else {
                arrayList.get((int)(arrayList.size() - 1)).to = ordersList.size() - 1;
            }
        }
        return arrayList;
    }

    private long getYearInMs(long l) {
        int n = SQTime.getFullYear((long)l);
        this.cal.set(n, 0, 1, 0, 0, 0);
        return this.cal.getTimeInMillis();
    }
}

