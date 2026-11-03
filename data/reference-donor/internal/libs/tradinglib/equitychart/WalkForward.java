/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.equitychart;

import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.equitychart.ChartDataset;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.Marker;
import com.strategyquant.tradinglib.equitychart.SubChart;
import com.strategyquant.tradinglib.equitychart.SubChartDataset;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForward {
    public static final Logger Log = LoggerFactory.getLogger(WalkForward.class);
    private int optFromTradeIndex = -1;
    private int optToTradeIndex = -1;
    private int runFromTradeIndex = -1;
    private int runToTradeIndex = -1;

    public void print(EquityChart equityChart, OrdersList ordersList, ResultsGroup resultsGroup, String string, String string2, byte by, byte by2) throws Exception {
        Object object;
        Object object2;
        Object object3;
        int n;
        WalkForwardMatrixResult walkForwardMatrixResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
        if (walkForwardMatrixResult == null) {
            return;
        }
        WalkForwardResult walkForwardResult = walkForwardMatrixResult.getWFResult(string2, true);
        if (walkForwardResult == null) {
            return;
        }
        MainChartDataset mainChartDataset = equityChart.getMainChartDatasets().get(0);
        long l = mainChartDataset.xVals[0];
        SubChart subChart = null;
        if (by2 == 127) {
            subChart = new SubChart("WalkForward");
            subChart.name = "WF Periods";
            equityChart.addSubChart(subChart);
        }
        if (string.equals("time")) {
            for (n = 0; n < walkForwardResult.wfPeriods.size(); ++n) {
                object3 = walkForwardResult.wfPeriods.get(n);
                if (by2 == 127) {
                    object2 = new SubChartDataset("WalkForwardOpt" + n, 2);
                    ((ChartDataset)object2).addValue(((WalkForwardPeriod)object3).optimizeFrom, n + 1);
                    ((ChartDataset)object2).addValue(((WalkForwardPeriod)object3).optimizeTo, n + 1);
                    ((SubChartDataset)object2).color = "#00ff00";
                    ((SubChartDataset)object2).thickness = 3;
                    subChart.addDataset((SubChartDataset)object2);
                    if (n != walkForwardResult.wfPeriods.size() - 1) {
                        object = new SubChartDataset("WalkForwardRun" + n, 2);
                        ((ChartDataset)object).addValue(((WalkForwardPeriod)object3).runFrom, n + 1);
                        ((ChartDataset)object).addValue(((WalkForwardPeriod)object3).runTo, n + 1);
                        ((SubChartDataset)object).color = "#ff0000";
                        ((SubChartDataset)object).thickness = 3;
                        subChart.addDataset((SubChartDataset)object);
                    }
                    object = new Marker();
                    ((Marker)object).x = ((WalkForwardPeriod)object3).runFrom;
                    equityChart.addMarker((Marker)object);
                    continue;
                }
                if (by2 != 20) continue;
                object2 = new Marker();
                ((Marker)object2).x = ((WalkForwardPeriod)object3).runFrom < l ? l : ((WalkForwardPeriod)object3).runFrom;
                equityChart.addMarker((Marker)object2);
            }
        } else {
            for (n = 0; n < walkForwardResult.wfPeriods.size(); ++n) {
                object3 = walkForwardResult.wfPeriods.get(n);
                this.computeTradeIndexes(ordersList, (WalkForwardPeriod)object3);
                if (by2 == 127) {
                    object2 = new SubChartDataset("WalkForwardOpt" + n, 2);
                    ((ChartDataset)object2).addValue(this.optFromTradeIndex, n + 1);
                    ((ChartDataset)object2).addValue(this.optToTradeIndex, n + 1);
                    ((SubChartDataset)object2).color = "#00ff00";
                    ((SubChartDataset)object2).thickness = 3;
                    subChart.addDataset((SubChartDataset)object2);
                    if (n != walkForwardResult.wfPeriods.size() - 1) {
                        object = new SubChartDataset("WalkForwardRun" + n, 2);
                        ((ChartDataset)object).addValue(this.runFromTradeIndex, n + 1);
                        ((ChartDataset)object).addValue(this.runToTradeIndex, n + 1);
                        ((SubChartDataset)object).color = "#ff0000";
                        ((SubChartDataset)object).thickness = 3;
                        subChart.addDataset((SubChartDataset)object);
                    }
                    object = new Marker();
                    ((Marker)object).x = this.runFromTradeIndex;
                    equityChart.addMarker((Marker)object);
                    continue;
                }
                if (by2 != 20) continue;
                object2 = new Marker();
                ((Marker)object2).x = this.runFromTradeIndex;
                equityChart.addMarker((Marker)object2);
            }
        }
        if (string.equals("time") || by2 == 127 || by2 == 10) {
            Object object4 = resultsGroup.orders().filter(resultsGroup.getMainResultKey(), by, (byte)127, true);
            if (by2 == 10 || by2 == 20) {
                object3 = new OrdersList("ordersOriginal");
                object2 = walkForwardResult.wfPeriods.get(0);
                for (int i = 0; i < ((OrdersList)object4).size(); ++i) {
                    Order order = ((OrdersList)object4).get(i);
                    if (by2 == 10) {
                        if (order.CloseTime > ((WalkForwardPeriod)object2).optimizeTo) break;
                        ((OrdersList)object3).add(((OrdersList)object4).get(i));
                        continue;
                    }
                    if (order.CloseTime <= ((WalkForwardPeriod)object2).optimizeTo) continue;
                    ((OrdersList)object3).add(((OrdersList)object4).get(i));
                }
                object4 = object3;
            }
            object3 = EquityChartUtils.generateDataset((OrdersList)object4, string);
            ((MainChartDataset)object3).name = "Original strategy";
            ((MainChartDataset)object3).color = "#969696";
            ((MainChartDataset)object3).colorDark = "#969696";
            equityChart.addMainChartDataset((MainChartDataset)object3);
        }
    }

    private void computeTradeIndexes(OrdersList ordersList, WalkForwardPeriod walkForwardPeriod) {
        this.optFromTradeIndex = -1;
        this.optToTradeIndex = -1;
        this.runFromTradeIndex = -1;
        this.runToTradeIndex = -1;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order order = ordersList.get(i);
            if (order.CloseTime >= walkForwardPeriod.optimizeFrom && this.optFromTradeIndex == -1) {
                this.optFromTradeIndex = i;
            }
            if (order.CloseTime >= walkForwardPeriod.optimizeTo && this.optToTradeIndex == -1) {
                this.optToTradeIndex = i;
            }
            if (order.CloseTime >= walkForwardPeriod.runFrom && this.runFromTradeIndex == -1) {
                this.runFromTradeIndex = i;
            }
            if (order.CloseTime < walkForwardPeriod.runTo || this.runToTradeIndex != -1) continue;
            this.runToTradeIndex = i;
            break;
        }
        if (this.runToTradeIndex == -1) {
            this.runToTradeIndex = ordersList.size() - 1;
        }
        if (this.optToTradeIndex == -1) {
            this.optToTradeIndex = ordersList.size() - 1;
            this.runFromTradeIndex = ordersList.size() - 1;
        }
    }
}

