/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import java.util.ArrayList;

public class Points {
    public String SHOW_TRADE_PEAKS = "grow";
    public String SHOW_ALL_POINTS = "all";

    public void print(EquityChart equityChart, String string, String string2) {
        ArrayList<MainChartDataset> arrayList = equityChart.getMainChartDatasets();
        if (arrayList.isEmpty()) {
            return;
        }
        MainChartDataset mainChartDataset = arrayList.get(0);
        int n = this.getSize(mainChartDataset, string, string2);
        MainChartDataset mainChartDataset2 = new MainChartDataset("Points", n);
        mainChartDataset2.name = "Trade points";
        mainChartDataset2.type = "point";
        mainChartDataset2.color = string.equals(this.SHOW_ALL_POINTS) ? "#FF0000" : "#00ff00";
        for (int i = 0; i < mainChartDataset.length; ++i) {
            long l = mainChartDataset.xVals[i];
            double d = mainChartDataset.yVals[i];
            if (string.equals(this.SHOW_TRADE_PEAKS)) {
                if (mainChartDataset2.index >= 0 && !(mainChartDataset2.yVals[mainChartDataset2.index] < d)) continue;
                mainChartDataset2.addValue(l, d);
                continue;
            }
            if (string2.equals("time")) {
                if (i != 0 && mainChartDataset.yVals[i - 1] == d) continue;
                mainChartDataset2.addValue(l, d);
                continue;
            }
            mainChartDataset2.addValue(l, d);
        }
        equityChart.addMainChartDataset(mainChartDataset2);
    }

    private int getSize(MainChartDataset mainChartDataset, String string, String string2) {
        int n = 0;
        double d = 0.0;
        if (string.equals(this.SHOW_ALL_POINTS)) {
            if (string2.equals("time")) {
                for (int i = 0; i < mainChartDataset.length; ++i) {
                    if (i != 0 && mainChartDataset.yVals[i - 1] == mainChartDataset.yVals[i]) continue;
                    ++n;
                }
            } else {
                n = mainChartDataset.length;
            }
        } else {
            for (int i = 0; i < mainChartDataset.length; ++i) {
                if (i != 0 && !(d < mainChartDataset.yVals[i])) continue;
                d = mainChartDataset.yVals[i];
                ++n;
            }
        }
        return n;
    }
}

