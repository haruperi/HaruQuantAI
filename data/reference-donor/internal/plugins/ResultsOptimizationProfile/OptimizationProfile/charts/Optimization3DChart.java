/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 *  it.unimi.dsi.fastutil.doubles.DoubleArrayList
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.charts;

import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.doubles.DoubleArrayList;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.Collections;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Optimization3DChart {
    private static final Logger Log = LoggerFactory.getLogger(Optimization3DChart.class);

    public JSONObject print(ResultsGroup rg, String xaxis, String yaxis, String zaxis, String type) throws Exception {
        double yValue;
        double xValue;
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
        DatabankColumn databankColumn = (DatabankColumn)DatabankColumns.get().findClassByName(zaxis);
        JSONObject data = new JSONObject();
        JSONArray values = new JSONArray();
        DoubleArrayList xValues = new DoubleArrayList();
        DoubleArrayList yValues = new DoubleArrayList();
        String bestStrategyName = null;
        for (int i = 0; i < localOptimizations.size(); ++i) {
            OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
            Int2DoubleOpenHashMap params = result.parseParams();
            if (params.containsKey(xaxis.hashCode()) && !xValues.contains(xValue = params.get(xaxis.hashCode()))) {
                xValues.add(xValue);
            }
            if (!params.containsKey(yaxis.hashCode()) || yValues.contains(yValue = params.get(yaxis.hashCode()))) continue;
            yValues.add(yValue);
        }
        Collections.sort(xValues);
        Collections.sort(yValues);
        double bestZValue = -9.99999999E8;
        double zmax = Double.MAX_VALUE;
        double zmin = Double.MAX_VALUE;
        Group[][] groups = new Group[xValues.size()][yValues.size()];
        for (int i = 0; i < localOptimizations.size(); ++i) {
            OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
            Int2DoubleOpenHashMap params = result.parseParams();
            for (int x = 0; x < xValues.size(); ++x) {
                for (int y = 0; y < yValues.size(); ++y) {
                    xValue = xValues.get(x);
                    yValue = yValues.get(y);
                    if (!params.containsKey(xaxis.hashCode()) || params.get(xaxis.hashCode()) != xValue || !params.containsKey(yaxis.hashCode()) || params.get(yaxis.hashCode()) != yValue) continue;
                    double zValue = databankColumn.getNumericValue(result.stats);
                    if (zValue > bestZValue) {
                        bestZValue = zValue;
                        bestStrategyName = rg.getName();
                    }
                    if (zmin == Double.MAX_VALUE || zmin > zValue) {
                        zmin = zValue;
                    }
                    if (zmax == Double.MAX_VALUE || zmax < zValue) {
                        zmax = zValue;
                    }
                    if (groups[x][y] == null) {
                        groups[x][y] = new Group();
                    }
                    groups[x][y].add(zValue, result.params);
                }
            }
        }
        for (int x = 0; x < xValues.size(); ++x) {
            for (int y = 0; y < yValues.size(); ++y) {
                int i;
                Group group = groups[x][y];
                if (group == null) continue;
                xValue = xValues.get(x);
                yValue = yValues.get(y);
                if (type.equals("top") || type.equals("surface") || type.equals("dot-color-one")) {
                    if (databankColumn.getValueType() == 1) {
                        i = group.getMinIndex();
                        values.put((Object)new JSONObject().put("x", xValue).put("y", yValue).put("z", group.zvalues[i]).put("style", group.zvalues[i]).put("str", (Object)rg.getName()).put("params", (Object)group.params[i]));
                        continue;
                    }
                    i = group.getMaxIndex();
                    values.put((Object)new JSONObject().put("x", xValue).put("y", yValue).put("z", group.zvalues[i]).put("style", group.zvalues[i]).put("str", (Object)rg.getName()).put("params", (Object)group.params[i]));
                    continue;
                }
                for (i = 0; i < group.size(); ++i) {
                    values.put((Object)new JSONObject().put("x", xValue).put("y", yValue).put("z", group.zvalues[i]).put("style", group.zvalues[i]).put("str", (Object)rg.getName()).put("params", (Object)group.params[i]));
                }
            }
        }
        data.put("values", (Object)values);
        data.put("xlabel", (Object)xaxis);
        data.put("ylabel", (Object)yaxis);
        data.put("zlabel", (Object)databankColumn.getName());
        data.put("zmin", zmin);
        data.put("zmax", zmax);
        data.put("bestStrategyName", bestStrategyName);
        data.put("reverseColorScale", databankColumn.getValueType() == 2);
        return data;
    }

    public boolean has3DData(ResultsGroup resultsGroup) {
        OptimizationProfile optimizationProfile = resultsGroup.getOptimizationProfile();
        if (optimizationProfile == null) {
            return false;
        }
        ObjectArrayList optimizations = optimizationProfile.getOptimizations();
        return optimizations != null && optimizations.size() != 0;
    }

    private class Group {
        private static final int COUNT = 5;
        public double[] zvalues = new double[5];
        public String[] params = new String[5];
        private int index = -1;

        private Group() {
        }

        public void add(Double zvalue, String params) {
            if (this.index < 4) {
                ++this.index;
                this.zvalues[this.index] = zvalue;
                this.params[this.index] = params;
            } else {
                int minIndex = 0;
                int maxIndex = 0;
                for (int i = 0; i < this.size(); ++i) {
                    if (this.zvalues[i] < this.zvalues[minIndex]) {
                        minIndex = i;
                    }
                    if (!(this.zvalues[i] > this.zvalues[maxIndex])) continue;
                    maxIndex = i;
                }
                if (zvalue < this.zvalues[minIndex]) {
                    this.zvalues[minIndex] = zvalue;
                    this.params[minIndex] = params;
                } else if (zvalue > this.zvalues[maxIndex]) {
                    this.zvalues[maxIndex] = zvalue;
                    this.params[maxIndex] = params;
                }
            }
        }

        public int getMaxIndex() {
            int maxIndex = 0;
            for (int i = 0; i < this.size(); ++i) {
                if (!(this.zvalues[i] > this.zvalues[maxIndex])) continue;
                maxIndex = i;
            }
            return maxIndex;
        }

        public int getMinIndex() {
            int minIndex = 0;
            for (int i = 0; i < this.size(); ++i) {
                if (!(this.zvalues[i] < this.zvalues[minIndex])) continue;
                minIndex = i;
            }
            return minIndex;
        }

        public int size() {
            return this.index + 1;
        }
    }
}

