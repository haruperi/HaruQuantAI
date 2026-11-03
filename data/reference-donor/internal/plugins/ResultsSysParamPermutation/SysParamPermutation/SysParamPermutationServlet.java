/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.optimization.SysParamPermutationsCharts
 *  com.strategyquant.tradinglib.optimization.SysParamPermutationsTable
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.SysParamPermutation;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.optimization.SysParamPermutationsCharts;
import com.strategyquant.tradinglib.optimization.SysParamPermutationsTable;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SysParamPermutationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SysParamPermutationServlet.class);
    private static final String LOCK_SYSPARAMPERMSERVLET = "SysParamPermutationServlet";
    private static IResultsGroupProvider rgProvider;

    public SysParamPermutationServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(args);
            }
            case "printTable": {
                return this.onPrintTable(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONObject loadLastSettings() throws Exception {
        JSONObject response = new JSONObject();
        String charts = MainApp.settings().get("SPPCharts", "NetProfit,Drawdown,DrawdownPct,ReturnDDRatio,SharpeRatio,CAGR");
        response.put("charts", (Object)SQUtils.toJSONArray((String)charts));
        String stats = MainApp.settings().get("SPPStats", "NetProfit,Drawdown,DrawdownPct,ReturnDDRatio,SharpeRatio,CAGR");
        response.put("stats", (Object)SQUtils.toJSONArray((String)stats));
        return response;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintTable(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"statsKeys"});
        String statsKeys = this.tryGetParamValue(parameterMap, "statsKeys");
        String[] statsItems = statsKeys.split(",");
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_SYSPARAMPERMSERVLET);
            OptimizationProfile optimizationProfile = resultsGroup.getOptimizationProfile();
            if (optimizationProfile == null) {
                response.put("stats", (Object)new JSONArray());
                response.put("success", (Object)"ok");
                String string = response.toString();
                return string;
            }
            SysParamPermutationsTable table = optimizationProfile.getSysParamPermutationsTable();
            JSONArray statsArray = new JSONArray();
            for (int i = 0; i < statsItems.length; ++i) {
                String statsKey = statsItems[i];
                DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(statsKey);
                double median = table.getMedian(statsKey);
                double origValue = table.getOrigValue(statsKey);
                double origMedianPct = origValue / median * 100.0;
                JSONObject valuesObj = new JSONObject();
                valuesObj.put("median", (Object)column.printPlValue(median, (byte)10));
                valuesObj.put("orig", (Object)column.printPlValue(origValue, (byte)10));
                valuesObj.put("origMedianPct", (Object)PlTypes.printPL((double)origMedianPct, (byte)20));
                statsArray.put((Object)valuesObj);
            }
            MainApp.settings().set("SPPStats", statsKeys);
            response.put("stats", (Object)statsArray);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrintTable: " + e.getMessage());
            String string = SysParamPermutationServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            Log.error("onPrintTable: " + e.getMessage());
            String string = SysParamPermutationServlet.apiErrorJSONNoLog((String)"SysParamPermutation error", (Exception)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_SYSPARAMPERMSERVLET);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"statsKeys"});
        String statsKeys = this.tryGetParamValue(parameterMap, "statsKeys");
        String[] statsItems = statsKeys.split(",");
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_SYSPARAMPERMSERVLET);
            OptimizationProfile optimizationProfile = resultsGroup.getOptimizationProfile();
            if (optimizationProfile == null) {
                response.put("charts", (Object)new JSONArray());
                response.put("success", (Object)"ok");
                String string = response.toString();
                return string;
            }
            SysParamPermutationsCharts sppCharts = optimizationProfile.getSysParamPermutationsCharts();
            JSONArray charts = new JSONArray();
            for (int i = 0; i < statsItems.length; ++i) {
                JSONObject chart = sppCharts.get(statsItems[i]);
                charts.put((Object)chart);
            }
            MainApp.settings().set("SPPCharts", statsKeys);
            response.put("charts", (Object)charts);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = SysParamPermutationServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            Log.error("onPrint: " + e.getMessage());
            String string = SysParamPermutationServlet.apiErrorJSONNoLog((String)"SysParamPermutation error", (Exception)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_SYSPARAMPERMSERVLET);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

