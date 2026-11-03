/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.EquityChartUtils
 *  com.strategyquant.tradinglib.equitychart.MainChartDataset
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.RobustnessTests;

import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.robustnesstests.RobustnessOrdersValues;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RTChart {
    private static final Logger Log = LoggerFactory.getLogger(RTChart.class);

    public JSONObject print(Result result, String methodName, int width, int height) {
        EquityChart chart = new EquityChart();
        MainChartDataset dataset = null;
        RobustnessResults rr = (RobustnessResults)result.get("RobustnessOriginalResults");
        if (rr != null) {
            dataset = this.createSeries("Original", rr.getOrdersValues(), 0);
            dataset.filled = true;
            dataset.fillColor = "#DAF5FF";
            dataset.fillNegativeColor = "#F49C9C";
            dataset.thickness = 3;
            chart.addMainChartDataset(dataset);
        }
        int numberOfSimulations = result.getInt(methodName + "_NumberOfSimulations");
        for (int i = 0; i < numberOfSimulations; ++i) {
            rr = result.getMCSimulation(methodName, i);
            if (rr == null || (dataset = this.createSeries("Simulation " + i, rr.getOrdersValues(), i + 1)) == null) continue;
            chart.addMainChartDataset(dataset);
        }
        return chart.toJSON();
    }

    private MainChartDataset createSeries(String name, RobustnessOrdersValues ordersValues, int simulationNumber) {
        double pl = 0.0;
        int[] values = ordersValues.arr();
        if (values == null) {
            return null;
        }
        MainChartDataset dataset = new MainChartDataset("RobustnessTests", values.length);
        dataset.name = name;
        dataset.title = name;
        dataset.color = EquityChartUtils.getColor((int)simulationNumber, (boolean)false);
        dataset.colorDark = EquityChartUtils.getColor((int)simulationNumber, (boolean)true);
        for (int i = 0; i < values.length; ++i) {
            dataset.addValue((long)i, pl += (double)values[i] / 100.0);
        }
        return dataset;
    }
}

