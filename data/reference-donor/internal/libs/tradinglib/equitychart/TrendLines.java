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
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import java.util.ArrayList;
import java.util.List;

public class TrendLines {
    public void print(EquityChart equityChart, List<TimePeriod> list, String string) {
        if (list == null || list.isEmpty()) {
            return;
        }
        int n = 0;
        boolean bl = true;
        MainChartDataset mainChartDataset = new MainChartDataset("TrendLines", list.size() + 1);
        mainChartDataset.color = "#FF0000";
        ArrayList<MainChartDataset> arrayList = equityChart.getMainChartDatasets();
        if (arrayList.isEmpty()) {
            return;
        }
        MainChartDataset mainChartDataset2 = arrayList.get(0);
        for (int i = 0; i < mainChartDataset2.length; ++i) {
            long l = mainChartDataset2.xVals[i];
            double d = mainChartDataset2.yVals[i];
            TimePeriod timePeriod = list.get(n);
            if (string.equals("time")) {
                l = SQTime.getDateInMs((long)l);
            }
            if (bl) {
                mainChartDataset.addValue(l, d);
                bl = false;
                continue;
            }
            if (l != timePeriod.to && l <= timePeriod.to) continue;
            mainChartDataset.addValue(l, d);
            if (++n == list.size()) break;
        }
        if (mainChartDataset.getSize() > 1 && mainChartDataset.xVals[mainChartDataset.getSize() - 1] == 0L && mainChartDataset.yVals[mainChartDataset.getSize() - 1] == 0.0) {
            mainChartDataset.xVals[mainChartDataset.getSize() - 1] = mainChartDataset.xVals[mainChartDataset.getSize() - 2];
            mainChartDataset.yVals[mainChartDataset.getSize() - 1] = mainChartDataset.yVals[mainChartDataset.getSize() - 2];
        }
        equityChart.addMainChartDataset(mainChartDataset);
    }
}

