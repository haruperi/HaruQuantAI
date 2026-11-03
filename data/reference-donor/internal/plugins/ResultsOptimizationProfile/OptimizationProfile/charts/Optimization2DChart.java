/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.BarChart
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.charts;

import com.strategyquant.tradinglib.BarChart;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Collections;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Optimization2DChart {
    private static final Logger Log = LoggerFactory.getLogger(Optimization2DChart.class);

    public JSONObject print(ResultsGroup rg, String xaxis, String yaxis) throws Exception {
        double xValue;
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(yaxis);
        DoubleArrayList xValues = new DoubleArrayList();
        for (int i = 0; i < localOptimizations.size(); ++i) {
            OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
            Int2DoubleOpenHashMap params = result.parseParams();
            if (!params.containsKey(xaxis.hashCode()) || xValues.contains(xValue = params.get(xaxis.hashCode()))) continue;
            xValues.add(xValue);
        }
        Collections.sort(xValues);
        BarChart chart = new BarChart();
        chart.maxXTicksLimit = 10;
        chart.yAxisTitle = databankColumn.getName();
        chart.xAxisTitle = xaxis;
        chart.tooltips = false;
        chart.disableEvents = true;
        boolean singleParamOpt = ((OptimizationTestResult)localOptimizations.get(0)).parseParams().size() == 1;
        chart.setCategoryColor("best", "#008000");
        if (!singleParamOpt) {
            chart.setCategoryColor("worst", "#E8383C");
        }
        for (int x = 0; x < xValues.size(); ++x) {
            xValue = xValues.get(x);
            double zmax = Double.MAX_VALUE;
            double zmin = Double.MAX_VALUE;
            for (int i = 0; i < localOptimizations.size(); ++i) {
                OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
                Int2DoubleOpenHashMap params = result.parseParams();
                if (!params.containsKey(xaxis.hashCode()) || params.get(xaxis.hashCode()) != xValue) continue;
                double zValue = databankColumn.getNumericValue(result.stats);
                if (zmin == Double.MAX_VALUE || zmin > zValue) {
                    zmin = zValue;
                }
                if (zmax != Double.MAX_VALUE && !(zmax < zValue)) continue;
                zmax = zValue;
            }
            if (databankColumn.getValueType() == 1) {
                chart.addValue("best", (Comparable)Double.valueOf(xValue), (Number)zmax);
                if (singleParamOpt) continue;
                chart.addValue("worst", (Comparable)Double.valueOf(xValue), (Number)zmin);
                continue;
            }
            chart.addValue("best", (Comparable)Double.valueOf(xValue), (Number)zmin);
            if (singleParamOpt) continue;
            chart.addValue("worst", (Comparable)Double.valueOf(xValue), (Number)zmax);
        }
        return chart.toJSON();
    }
}

