/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.OptimizationTestResult
 *  it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile.results;

import com.strategyquant.plugin.Results.impl.OptimizationProfile.results.OptComparatorByFitness;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.OptimizationTestResult;
import it.unimi.dsi.fastutil.ints.Int2DoubleOpenHashMap;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.ArrayList;
import java.util.Collections;
import org.json.JSONArray;
import org.json.JSONObject;

public class OptResults {
    public JSONArray print(ResultsGroup rg, String xaxis, String yaxis, String zaxis, String type, String chartType, DatabankTableView view) {
        OptimizationProfile optimizationProfile = rg.getOptimizationProfile();
        ObjectArrayList localOptimizations = optimizationProfile.getOptimizations().clone();
        Collections.sort(localOptimizations, new OptComparatorByFitness());
        JSONArray rows = new JSONArray();
        for (int i = 0; i < localOptimizations.size(); ++i) {
            OptimizationTestResult result = (OptimizationTestResult)localOptimizations.get(i);
            rows.put((Object)this.printRow(result, view, i, chartType, xaxis, yaxis));
            if (i == 500) break;
        }
        return rows;
    }

    private JSONObject printRow(OptimizationTestResult result, DatabankTableView view, int row, String chartType, String xaxis, String yaxis) {
        JSONObject obj = new JSONObject();
        JSONArray data = new JSONArray();
        ArrayList columns = view.columns;
        for (int i = 0; i < columns.size(); ++i) {
            DatabankColumn column = ((DatabankTableColumnEntry)columns.get((int)i)).tableColumn;
            try {
                String formattedValue = column.printValue(result.stats);
                data.put((Object)formattedValue);
                continue;
            }
            catch (Exception e) {
                data.put((Object)"N/A");
            }
        }
        Int2DoubleOpenHashMap params = result.parseParams();
        if (chartType.equals("3D")) {
            if (params.containsKey(xaxis.hashCode())) {
                double xValue = params.get(xaxis.hashCode());
                data.put(xValue);
            } else {
                data.put((Object)"N/A");
            }
            if (params.containsKey(yaxis.hashCode())) {
                double yValue = params.get(yaxis.hashCode());
                data.put(yValue);
            } else {
                data.put((Object)"N/A");
            }
        } else if (chartType.equals("2D")) {
            if (params.containsKey(xaxis.hashCode())) {
                double xValue = params.get(xaxis.hashCode());
                data.put(xValue);
            } else {
                data.put((Object)"N/A");
            }
        }
        obj.put("id", (Object)("r" + row));
        obj.put("data", (Object)data);
        return obj;
    }
}

