/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.longs.Long2FloatMap$Entry
 *  it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import it.unimi.dsi.fastutil.longs.Long2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.longs.Long2FloatMap;
import it.unimi.dsi.fastutil.longs.Long2FloatRBTreeMap;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Equity {
    public static final Logger Log = LoggerFactory.getLogger(Equity.class);
    long msFrom;
    long msTo;
    int daysCount;

    public void print(EquityChart equityChart, OrdersList ordersList, ResultsGroup resultsGroup, String string, String string2, byte by, byte by2, String string3) {
        if (by != 0 || by2 != 127) {
            return;
        }
        if (string3.equals("daily")) {
            this.printDailyEquity(equityChart, ordersList, resultsGroup, string, string2, by, by2);
        } else if (string3.equals("maemfe")) {
            this.printMaemfe(equityChart, ordersList, resultsGroup, string, string2, by, by2);
        }
    }

    public void printMaemfe(EquityChart equityChart, OrdersList ordersList, ResultsGroup resultsGroup, String string, String string2, byte by, byte by2) {
        try {
            MainChartDataset mainChartDataset = null;
            MainChartDataset mainChartDataset2 = null;
            if (!this.containsMaemfe(ordersList)) {
                return;
            }
            if (string.equals("time")) {
                this.parseDateRange(equityChart);
                mainChartDataset = new MainChartDataset("MAE", this.daysCount);
                mainChartDataset2 = new MainChartDataset("MFE", this.daysCount);
                this.maemfeByTime(mainChartDataset, mainChartDataset2, ordersList);
            } else {
                mainChartDataset = new MainChartDataset("MAE", ordersList.size());
                mainChartDataset2 = new MainChartDataset("MFE", ordersList.size());
                this.maemfeByTrades(mainChartDataset, mainChartDataset2, ordersList);
            }
            mainChartDataset.title = "MAE";
            mainChartDataset.color = "red";
            equityChart.addMainChartDataset(mainChartDataset);
            mainChartDataset2.title = "MFE";
            mainChartDataset2.color = "green";
            equityChart.addMainChartDataset(mainChartDataset2);
        }
        catch (Exception exception) {
            Log.error("Error while rendering Daily Equity curve. Exc.", (Throwable)exception);
        }
    }

    private boolean containsMaemfe(OrdersList ordersList) {
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            if (order.MAE == 0.0f && order.MFE == 0.0f) continue;
            return true;
        }
        return false;
    }

    private void maemfeByTrades(MainChartDataset mainChartDataset, MainChartDataset mainChartDataset2, OrdersList ordersList) {
        double d = 0.0;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            mainChartDataset.addValue(i, d + (double)(order.MAE * -1.0f));
            mainChartDataset2.addValue(i, d + (double)order.MFE);
            d += (double)order.PL;
        }
    }

    private void maemfeByTime(MainChartDataset mainChartDataset, MainChartDataset mainChartDataset2, OrdersList ordersList) {
        long l;
        Long2DoubleOpenHashMap long2DoubleOpenHashMap = new Long2DoubleOpenHashMap();
        Long2DoubleOpenHashMap long2DoubleOpenHashMap2 = new Long2DoubleOpenHashMap();
        Long2DoubleOpenHashMap long2DoubleOpenHashMap3 = new Long2DoubleOpenHashMap();
        double d = 0.0;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            d += (double)order.PL;
            l = SQTime.getDateInMs((long)order.CloseTime);
            if (!long2DoubleOpenHashMap2.containsKey(l)) {
                long2DoubleOpenHashMap2.put(l, 0.0);
                long2DoubleOpenHashMap3.put(l, 0.0);
            }
            long2DoubleOpenHashMap.put(l, d);
            long2DoubleOpenHashMap2.put(l, long2DoubleOpenHashMap2.get(l) + (double)(order.MAE * -1.0f));
            long2DoubleOpenHashMap3.put(l, long2DoubleOpenHashMap3.get(l) + (double)order.MFE);
        }
        l = SQTime.getDateInMs((long)this.msFrom);
        double d2 = 0.0;
        do {
            if (long2DoubleOpenHashMap.containsKey(l)) {
                mainChartDataset.addValue(l, d2 + long2DoubleOpenHashMap2.get(l));
                mainChartDataset2.addValue(l, d2 + long2DoubleOpenHashMap3.get(l));
                d2 = long2DoubleOpenHashMap.get(l);
                continue;
            }
            if (mainChartDataset.index < 0) {
                mainChartDataset.addValue(l, 0.0);
                mainChartDataset2.addValue(l, 0.0);
                continue;
            }
            mainChartDataset.addValue(l, mainChartDataset.yVals[mainChartDataset.index]);
            mainChartDataset2.addValue(l, mainChartDataset2.yVals[mainChartDataset2.index]);
        } while ((l = SQTime.addDays((long)l, (int)1)) <= this.msTo);
    }

    public void printDailyEquity(EquityChart equityChart, OrdersList ordersList, ResultsGroup resultsGroup, String string, String string2, byte by, byte by2) {
        try {
            Result result = resultsGroup.subResult(string2);
            Long2FloatRBTreeMap long2FloatRBTreeMap = result.getWorstDailyEquity();
            if (long2FloatRBTreeMap == null || long2FloatRBTreeMap.isEmpty() || long2FloatRBTreeMap.size() < 5) {
                return;
            }
            MainChartDataset mainChartDataset = null;
            if (string.equals("time")) {
                if (resultsGroup.isStockpickerStrategy()) {
                    mainChartDataset = new MainChartDataset("DailyEquity", long2FloatRBTreeMap.size());
                    this.dailyEquityByTimeAll(mainChartDataset, long2FloatRBTreeMap);
                } else {
                    this.parseDateRange(equityChart);
                    mainChartDataset = new MainChartDataset("DailyEquity", this.daysCount);
                    this.dailyEquityByTime(mainChartDataset, long2FloatRBTreeMap);
                }
            } else {
                mainChartDataset = new MainChartDataset("DailyEquity", ordersList.size());
                this.dailyEquityByTrades(mainChartDataset, long2FloatRBTreeMap, ordersList);
            }
            mainChartDataset.title = "Daily Equity";
            mainChartDataset.color = "red";
            equityChart.addMainChartDataset(mainChartDataset);
        }
        catch (Exception exception) {
            Log.error("Error while rendering Daily Equity curve. Exc.", (Throwable)exception);
        }
    }

    private void dailyEquityByTimeAll(MainChartDataset mainChartDataset, Long2FloatRBTreeMap long2FloatRBTreeMap) {
        for (Long2FloatMap.Entry entry : long2FloatRBTreeMap.long2FloatEntrySet()) {
            long l = entry.getLongKey();
            float f = entry.getFloatValue();
            mainChartDataset.addValue(l, f);
        }
    }

    private void dailyEquityByTrades(MainChartDataset mainChartDataset, Long2FloatRBTreeMap long2FloatRBTreeMap, OrdersList ordersList) {
        double d = 3.4028234663852886E38;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            double d2 = this.getWorstEquity(order.OpenTime, order.CloseTime, long2FloatRBTreeMap);
            if (d2 == 3.4028234663852886E38) {
                d2 = d;
            } else {
                d = d2;
            }
            mainChartDataset.addValue(i, d2);
        }
    }

    private double getWorstEquity(long l, long l2, Long2FloatRBTreeMap long2FloatRBTreeMap) {
        double d = 0.0;
        long l3 = SQTime.getDateInMs((long)l);
        boolean bl = true;
        do {
            if (!long2FloatRBTreeMap.containsKey(l3) || !bl && !((double)long2FloatRBTreeMap.get(l3) < d)) continue;
            d = long2FloatRBTreeMap.get(l3);
            bl = false;
        } while ((l3 = SQTime.addDays((long)l3, (int)1)) <= l2);
        return d;
    }

    private void dailyEquityByTime(MainChartDataset mainChartDataset, Long2FloatRBTreeMap long2FloatRBTreeMap) throws Exception {
        if (mainChartDataset.length == 0) {
            return;
        }
        long l = SQTime.getDateInMs((long)this.msFrom);
        double d = 3.4028234663852886E38;
        do {
            if (long2FloatRBTreeMap.containsKey(l)) {
                double d2 = long2FloatRBTreeMap.get(l);
                if (d2 == 3.4028234663852886E38) {
                    d2 = d;
                } else {
                    d = d2;
                }
                if (d2 == 3.4028234663852886E38) {
                    d2 = 0.0;
                }
                mainChartDataset.addValue(l, d2);
                continue;
            }
            if (mainChartDataset.index < 0) {
                mainChartDataset.addValue(l, 0.0);
                continue;
            }
            mainChartDataset.addValue(l, mainChartDataset.yVals[mainChartDataset.index]);
        } while ((l = SQTime.addDays((long)l, (int)1)) <= this.msTo);
    }

    private void parseDateRange(EquityChart equityChart) throws Exception {
        ArrayList<MainChartDataset> arrayList = equityChart.getMainChartDatasets();
        if (arrayList.isEmpty()) {
            throw new Exception(L.t((String)"Cannot get start-end time for computing daily equity.", (Object[])new Object[0]));
        }
        MainChartDataset mainChartDataset = arrayList.get(0);
        if (mainChartDataset.length == 0) {
            this.msFrom = -1L;
            this.msTo = -1L;
            this.daysCount = 0;
        } else {
            this.msFrom = mainChartDataset.xVals[0];
            this.msTo = mainChartDataset.xVals[mainChartDataset.xVals.length - 1];
            this.daysCount = EquityChartUtils.getDaysBetween(this.msFrom, this.msTo);
        }
    }
}

