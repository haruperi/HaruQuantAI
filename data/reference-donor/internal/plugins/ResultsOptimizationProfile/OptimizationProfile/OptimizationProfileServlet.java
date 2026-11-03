/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.optimization.OptProfileChecksLevels
 *  com.strategyquant.tradinglib.optimization.OptimizationProfile
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.OptimizationProfile;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.charts.Optimization2DChart;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.charts.Optimization3DChart;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.charts.OptimizationScatterChart;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.results.OptResults;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.results.OptResultsExport;
import com.strategyquant.plugin.Results.impl.OptimizationProfile.results.OptResultsViews;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.optimization.OptProfileChecksLevels;
import com.strategyquant.tradinglib.optimization.OptimizationProfile;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationProfileServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(OptimizationProfileServlet.class);
    private static final String LOCK_OPTPROFSERVLET = "OptimizationProfileServlet";
    private IResultsGroupProvider rgProvider;
    private JSONArray columnValues = null;
    private Optimization3DChart optimization3d = null;
    private Optimization2DChart optimization2d = null;
    private OptimizationScatterChart optimizationScatter = null;
    private OptResultsViews resultsViews;
    private OptResults results;

    public OptimizationProfileServlet(IResultsGroupProvider rgProvider) {
        this.rgProvider = rgProvider;
        this.optimization3d = new Optimization3DChart();
        this.optimization2d = new Optimization2DChart();
        this.optimizationScatter = new OptimizationScatterChart();
        this.resultsViews = new OptResultsViews(MainApp.getDataPath() + "/user/settings/views/optimizationProfile");
        this.results = new OptResults();
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        if (command.startsWith("views")) {
            return this.resultsViews.execute(command, parameterMap, method);
        }
        switch (command) {
            case "print": {
                return this.onPrint(parameterMap);
            }
            case "printChart": {
                return this.onPrintChart(parameterMap);
            }
            case "printResults": {
                return this.onPrintResults(parameterMap);
            }
            case "getAvailableParams": {
                return this.onGetAvailableParams(parameterMap);
            }
            case "export": {
                return this.onExport(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        OptProfileChecksLevels checksLevels = new OptProfileChecksLevels();
        checksLevels.evalProfitOptCheck = Boolean.parseBoolean(parameterMap.get("evalProfitOptCheck")[0]);
        checksLevels.evalAvgProfitCheck = Boolean.parseBoolean(parameterMap.get("evalAvgProfitCheck")[0]);
        checksLevels.evalUniformDistrCheck = Boolean.parseBoolean(parameterMap.get("evalUniformDistrCheck")[0]);
        checksLevels.evalTopProfitCheck = Boolean.parseBoolean(parameterMap.get("evalTopProfitCheck")[0]);
        checksLevels.profitableOptPct = Integer.parseInt(parameterMap.get("profitOptPct")[0]);
        checksLevels.avgProfit = Double.parseDouble(parameterMap.get("avgProfit")[0]);
        checksLevels.uniformDistrChanges = Integer.parseInt(parameterMap.get("uniformDistrChanges")[0]);
        checksLevels.stdevAvgProfit = Double.parseDouble(parameterMap.get("stdevAvgProfit")[0]);
        ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_OPTPROFSERVLET);
        try {
            OptimizationProfile optimizationProfile = resultsGroup.getOptimizationProfile();
            response.put("simulations", (Object)optimizationProfile.printProfitableOptimizations());
            response.put("checks", (Object)optimizationProfile.printChecksResults(checksLevels));
            response.put("chart", (Object)optimizationProfile.printPerformanceDistributionChart());
            resultsGroup.specialValues().set("OptProfileChecksLevels", (Object)checksLevels);
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_OPTPROFSERVLET);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetAvailableParams(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = this.rgProvider.get(parameterMap, LOCK_OPTPROFSERVLET);
            OptimizationProfile optimizationProfile = resultsGroup.getOptimizationProfile();
            if (optimizationProfile == null) {
                throw new Exception(L.t((String)"No optimization results found.", (Object[])new Object[0]));
            }
            response.put("parameters", (Object)optimizationProfile.getAvailableParams());
            response.put("values", (Object)this.getColumnValues());
            OptProfileChecksLevels checksLevels = (OptProfileChecksLevels)resultsGroup.specialValues().get("OptProfileChecksLevels");
            if (checksLevels != null) {
                JSONObject checksObj = new JSONObject();
                checksObj.put("evalProfitOptCheck", checksLevels.evalProfitOptCheck);
                checksObj.put("evalAvgProfitCheck", checksLevels.evalAvgProfitCheck);
                checksObj.put("evalUniformDistrCheck", checksLevels.evalUniformDistrCheck);
                checksObj.put("evalTopProfitCheck", checksLevels.evalTopProfitCheck);
                checksObj.put("profitOptPct", checksLevels.profitableOptPct);
                checksObj.put("avgProfit", checksLevels.avgProfit);
                checksObj.put("uniformDistrChanges", checksLevels.uniformDistrChanges);
                checksObj.put("stdevAvgProfit", checksLevels.stdevAvgProfit);
                response.put("checks", (Object)checksObj);
            }
        }
        catch (RecordNotFoundException e) {
            Log.info("onGetAvailableParams: " + e.getMessage());
            String string = OptimizationProfileServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = OptimizationProfileServlet.apiErrorJSON((String)L.t((String)"Getting available params failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_OPTPROFSERVLET);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private synchronized JSONArray getColumnValues() {
        if (this.columnValues == null) {
            this.columnValues = new JSONArray();
            List columns = DatabankColumns.get().getAvailableClasses();
            for (DatabankColumn column : columns) {
                JSONObject columnObj = new JSONObject();
                columnObj.put("name", (Object)column.getName());
                columnObj.put("type", (Object)column.getClass().getSimpleName());
                this.columnValues.put((Object)columnObj);
            }
        }
        return this.columnValues;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintChart(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_OPTPROFSERVLET);
        try {
            this.checkParamExists(parameterMap, new String[]{"xaxis", "yaxis", "zaxis"});
            String xaxis = this.tryGetParamValue(parameterMap, "xaxis");
            String yaxis = this.tryGetParamValue(parameterMap, "yaxis");
            String zaxis = this.tryGetParamValue(parameterMap, "zaxis");
            if (!this.optimization3d.has3DData(resultsGroup)) {
                response.put("success", (Object)"ok");
                response.put("nochart", (Object)"ok");
                String string = response.toString();
                return string;
            }
            String type = this.tryGetParamValue(parameterMap, "type");
            String chartType = this.tryGetParamValue(parameterMap, "chart");
            JSONObject chart = null;
            if (chartType.equals("3D")) {
                chart = this.optimization3d.print(resultsGroup, xaxis, yaxis, zaxis, type);
            } else if (chartType.equals("2D")) {
                chart = this.optimization2d.print(resultsGroup, xaxis, zaxis);
            } else if (chartType.equals("Scatter")) {
                chart = this.optimizationScatter.print(resultsGroup, zaxis);
            } else {
                throw new Exception(L.t((String)"Invalid chart type. Must be one of: 3D, 2D, Scatter", (Object[])new Object[0]));
            }
            response.put("chart", (Object)chart);
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_OPTPROFSERVLET);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintResults(Map<String, String[]> parameterMap) throws Exception {
        ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_OPTPROFSERVLET);
        try {
            this.checkParamExists(parameterMap, new String[]{"xaxis", "yaxis", "zaxis"});
            String xaxis = this.tryGetParamValue(parameterMap, "xaxis");
            String yaxis = this.tryGetParamValue(parameterMap, "yaxis");
            String zaxis = this.tryGetParamValue(parameterMap, "zaxis");
            String type = this.tryGetParamValue(parameterMap, "type");
            String chartType = this.tryGetParamValue(parameterMap, "chart");
            JSONArray rows = new JSONArray();
            if (this.optimization3d.has3DData(resultsGroup)) {
                String viewName = parameterMap.get("view")[0].toString();
                DatabankTableView view = this.resultsViews.getViewByName(viewName);
                MainApp.settings().set("optProfileView", viewName);
                rows = this.results.print(resultsGroup, xaxis, yaxis, zaxis, type, chartType, view);
            }
            JSONObject response = new JSONObject();
            response.put("rows", (Object)rows);
            response.put("success", (Object)"ok");
            String string = response.toString();
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_OPTPROFSERVLET);
                resultsGroup = null;
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onExport(Map<String, String[]> parameterMap) throws Exception {
        ResultsGroup resultsGroup = this.rgProvider.get(parameterMap, LOCK_OPTPROFSERVLET);
        try {
            this.checkParamExists(parameterMap, new String[]{"xaxis", "yaxis", "zaxis"});
            String xaxis = this.tryGetParamValue(parameterMap, "xaxis");
            String yaxis = this.tryGetParamValue(parameterMap, "yaxis");
            String zaxis = this.tryGetParamValue(parameterMap, "zaxis");
            String type = this.tryGetParamValue(parameterMap, "type");
            String chartType = this.tryGetParamValue(parameterMap, "chart");
            String path = parameterMap.get("path")[0];
            boolean useComma = Boolean.parseBoolean(parameterMap.get("useComma")[0]);
            if (this.optimization3d.has3DData(resultsGroup)) {
                String viewName = parameterMap.get("view")[0].toString();
                DatabankTableView view = this.resultsViews.getViewByName(viewName);
                OptResultsExport export = new OptResultsExport();
                if (path.endsWith("xlsx")) {
                    export.toXlsx(path, useComma, resultsGroup, xaxis, yaxis, zaxis, type, chartType, view);
                } else {
                    export.toCsv(path, useComma, resultsGroup, xaxis, yaxis, zaxis, type, chartType, view);
                }
            } else {
                throw new Exception();
            }
            JSONObject responseJSON = new JSONObject();
            responseJSON.put("success", (Object)"Results exported.");
            String string = responseJSON.toString();
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_OPTPROFSERVLET);
                resultsGroup = null;
            }
        }
    }
}

