/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.TimePeriod
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.bestresults;

import com.strategyquant.lib.TimePeriod;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.Periods;
import com.strategyquant.tradinglib.equitychart.SampleMarkers;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import java.util.HashMap;
import java.util.List;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BestResultMiniChart {
    public static final Logger Log = LoggerFactory.getLogger(BestResultMiniChart.class);
    private EquityChart chart = null;
    private Periods periods = new Periods();
    private SampleMarkers sampleMarkers = new SampleMarkers();

    public BestResultMiniChart() {
        this.chart = new EquityChart();
        this.chart.setPLType((byte)10);
        this.chart.setDomainAxisType("trade");
        this.chart.hideYTitle(true);
    }

    public JSONObject print(ResultsGroup resultsGroup, byte by) {
        this.chart.reset();
        if (resultsGroup == null) {
            return null;
        }
        OrdersList ordersList = null;
        try {
            ordersList = resultsGroup.orders();
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return null;
        }
        if (ordersList == null) {
            return null;
        }
        try {
            String string = resultsGroup.getMainResultKey();
            OrdersList ordersList2 = resultsGroup.orders().filter(string, (byte)0, by, true);
            MainChartDataset mainChartDataset = EquityChartUtils.generateDataset(ordersList2, "trade");
            mainChartDataset.filled = true;
            mainChartDataset.fillColor = "#DAF5FF";
            mainChartDataset.fillColorDark = "#333C63";
            mainChartDataset.fillNegativeColor = "#F49C9C";
            mainChartDataset.thickness = 1;
            this.chart.addMainChartDataset(mainChartDataset);
            for (IEquityChartAddon iEquityChartAddon : SQPluginManager.getPlugins(IEquityChartAddon.class)) {
                try {
                    if (iEquityChartAddon.getName() == null || !iEquityChartAddon.getName().equals("Drawdown")) continue;
                    HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                    hashMap.put("drawdown", new String[]{"111"});
                    iEquityChartAddon.print(this.chart, resultsGroup, string, ordersList2, hashMap, "trade");
                    break;
                }
                catch (Exception exception) {
                    Log.error("Error while rendering EquityChart addon '" + iEquityChartAddon.getName() + "'. Exc.", (Throwable)exception);
                }
            }
            if (by == 127 || by == 10) {
                List<TimePeriod> list = this.periods.getAvailablePeriods(ordersList2, "trade");
                this.sampleMarkers.print(this.chart, list, false);
            }
            return this.chart.toJSON();
        }
        catch (Exception exception) {
            Log.error("Exc.", (Throwable)exception);
            return null;
        }
    }
}

