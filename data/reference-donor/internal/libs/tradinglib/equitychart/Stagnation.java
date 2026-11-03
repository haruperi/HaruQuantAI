/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.AreaFill;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Stagnation {
    public static final Logger Log = LoggerFactory.getLogger((String)"Stagnation");

    public void print(EquityChart equityChart, ResultsGroup resultsGroup, String string, OrdersList ordersList, byte by, byte by2, byte by3, String string2) {
        try {
            Result result = resultsGroup.subResult(string);
            int n = result.stats(by, by2, by3).getInt("Stagnation");
            long l = result.stats(by, by2, by3).getLong("StagnationFrom");
            long l2 = result.stats(by, by2, by3).getLong("StagnationTo");
            if (n == 0) {
                return;
            }
            long l3 = -1L;
            long l4 = -1L;
            if (string2.equals("time")) {
                l3 = l;
                l4 = l2;
            } else {
                for (int i = 0; i < ordersList.size(); ++i) {
                    if (ordersList.get((int)i).CloseTime >= l && l3 == -1L) {
                        l3 = i;
                    }
                    if (ordersList.get((int)i).CloseTime > l2) continue;
                    l4 = i;
                }
            }
            this.printMarker(equityChart, l3, l4, n);
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
        }
    }

    private void printMarker(EquityChart equityChart, long l, long l2, int n) {
        AreaFill areaFill = new AreaFill();
        areaFill.text = String.format("Max stagnation: %d days", n);
        areaFill.verticalAlign = "bottom";
        areaFill.color = "#FFC0C0";
        areaFill.textColor = "#FF0000";
        areaFill.colorDark = "#883030";
        areaFill.xFrom = l;
        areaFill.xTo = l2;
        equityChart.addArea(areaFill);
    }
}

