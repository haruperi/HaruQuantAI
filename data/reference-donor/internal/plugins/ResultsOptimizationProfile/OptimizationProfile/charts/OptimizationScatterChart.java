/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.ScatterChart
 *  com.strategyquant.tradinglib.charts.linechart.series.XYSeries
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.charts;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.ScatterChart;
import com.strategyquant.tradinglib.charts.linechart.series.XYSeries;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationScatterChart {
    private static final Logger Log = LoggerFactory.getLogger(OptimizationScatterChart.class);

    public JSONObject print(ResultsGroup rg, String yaxis) throws Exception {
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(yaxis);
        ScatterChart chart = new ScatterChart();
        XYSeries optSeries = new XYSeries("Optimizations");
        optSeries.color = "#383CE8";
        chart.addSeries(optSeries);
        chart.yAxisTitle = databankColumn.getName();
        chart.xAxisTitle = L.t((String)"Optimizations", (Object[])new Object[0]);
        chart.pointRadius = 3;
        chart.xAxisRangeMin = 0.0;
        chart.xAxisRangeMax = localOptimizations.size();
        for (int i = 0; i < localOptimizations.size(); ++i) {
            OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
            double yValue = databankColumn.getNumericValue(result.stats);
            optSeries.addValue((long)i, yValue);
        }
        return chart.toJSON();
    }
}

