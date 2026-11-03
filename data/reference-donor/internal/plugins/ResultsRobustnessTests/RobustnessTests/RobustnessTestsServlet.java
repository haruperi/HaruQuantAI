/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.RobustnessTests;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.plugin.Results.impl.RobustnessTests.ConfidenceLevels;
import com.strategyquant.plugin.Results.impl.RobustnessTests.RTChart;
import com.strategyquant.plugin.Results.impl.RobustnessTests.RiskOfRuins;
import com.strategyquant.plugin.Results.impl.RobustnessTests.views.RTViews;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.MonteCarloCrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RobustnessTestsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(RobustnessTestsServlet.class);
    private static final String LOCK_ROBTESTSERVLET = "RobustnessTestsServlet";
    private RTChart rtChart = new RTChart();
    private ConfidenceLevels confidenceLevels = new ConfidenceLevels();
    private RiskOfRuins riskOfRuins = new RiskOfRuins();
    private RTViews rtViews = new RTViews("rtView", MainApp.getDataPath() + "/user/settings/views/robustnessTests");
    private RTViews rtRRViews = new RTViews("rtRRView", MainApp.getDataPath() + "/user/settings/views/robustnessTestsRR");
    private static IResultsGroupProvider rgProvider;

    public RobustnessTestsServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        if (command.startsWith("views")) {
            String type = parameterMap.get("type")[0].toString();
            if (type.equals("rt")) {
                return this.rtViews.execute(command, parameterMap, method);
            }
            if (type.equals("rtRR")) {
                return this.rtRRViews.execute(command, parameterMap, method);
            }
        }
        switch (command) {
            case "printChart": {
                return this.onPrintChart(parameterMap);
            }
            case "printConfLevels": {
                return this.onPrintConfLevels(parameterMap);
            }
            case "printRiskOfRuinStats": {
                return this.onPrintRiskOfRuinStats(parameterMap);
            }
            case "getMethods": {
                return this.onGetMethods(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetMethods(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        boolean isAlgoWizard = false;
        try {
            isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        JSONArray methods = new JSONArray();
        ResultsGroup resultsGroup = rgProvider.get(parameterMap, LOCK_ROBTESTSERVLET);
        try {
            Result result = resultsGroup.mainResult();
            for (ICrossCheck plugin : SQPluginManager.getPlugins(ICrossCheck.class)) {
                if (!MonteCarloCrossCheckMethod.class.isAssignableFrom(plugin.getClass()) || result.getInt(plugin.getSettingName() + "_NumberOfSimulations") <= 0) continue;
                methods.put((Object)new JSONObject().put("value", (Object)plugin.getSettingName()).put("name", (Object)plugin.getName()));
            }
        }
        finally {
            resultsGroup.releaseLock(LOCK_ROBTESTSERVLET);
        }
        response.put("methods", (Object)methods);
        response.put("success", (Object)L.t((String)"Methods listed.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintChart(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"width", "height"});
        boolean isAlgoWizard = false;
        try {
            isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        ResultsGroup resultsGroup = null;
        String methodName = parameterMap.get("methodName")[0].toString();
        int _width = Integer.parseInt(parameterMap.get("width")[0]);
        int _height = Integer.parseInt(parameterMap.get("height")[0]);
        if (_width < 1 || _height < 1) {
            throw new Exception("Chart size is too small.");
        }
        boolean locked = false;
        if (isAlgoWizard) {
            resultsGroup = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{SQPaths.algoWizardStrategyPath});
        } else {
            this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy"});
            String _project = parameterMap.get("project")[0].toString();
            String _databank = parameterMap.get("databank")[0].toString();
            String _strategy = parameterMap.get("strategy")[0].toString();
            Databank databank = (Databank)ProjectEngine.get((String)_project).getDatabanks().get((Object)_databank);
            resultsGroup = databank.getLocked(_strategy, LOCK_ROBTESTSERVLET);
            locked = true;
        }
        try {
            String resultKey = resultsGroup.getMainResultKey();
            Result result = resultsGroup.subResult(resultKey);
            JSONObject response = new JSONObject();
            JSONObject chart = this.rtChart.print(result, methodName, _width, _height);
            response.put("chart", (Object)chart);
            response.put("success", (Object)"ok");
            String string = response.toString();
            return string;
        }
        finally {
            if (locked && resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_ROBTESTSERVLET);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintConfLevels(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"width", "height", "view"});
        boolean isAlgoWizard = false;
        try {
            isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        ResultsGroup resultsGroup = null;
        boolean locked = false;
        if (isAlgoWizard) {
            resultsGroup = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{SQPaths.algoWizardStrategyPath});
        } else {
            this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy"});
            String _project = parameterMap.get("project")[0].toString();
            String _databank = parameterMap.get("databank")[0].toString();
            String _strategy = parameterMap.get("strategy")[0].toString();
            Databank databank = (Databank)ProjectEngine.get((String)_project).getDatabanks().get((Object)_databank);
            resultsGroup = databank.getLocked(_strategy, LOCK_ROBTESTSERVLET);
            locked = true;
        }
        try {
            String methodName = parameterMap.get("methodName")[0].toString();
            String viewName = parameterMap.get("view")[0].toString();
            String resultKey = resultsGroup.getMainResultKey();
            Result result = resultsGroup.subResult(resultKey);
            JSONObject response = new JSONObject();
            DatabankTableView view = this.rtViews.getViewByName(viewName);
            MainApp.settings().set("rtView", viewName);
            int numberOfSimulations = result.getInt(methodName + "_NumberOfSimulations");
            String symbol = result.getString(methodName + "_Symbol");
            String timeframe = result.getString(methodName + "_TimeFrame");
            String dateRange = result.getString(methodName + "_DateRange");
            JSONObject settings = new JSONObject();
            if (symbol != null) {
                settings.put("data", (Object)(symbol + " / " + timeframe + ", " + dateRange));
            }
            settings.put("simulations", numberOfSimulations);
            JSONArray methodsJson = new JSONArray();
            settings.put("methods", (Object)methodsJson);
            String[] methods = (String[])result.get(methodName + "_Methods");
            if (methods != null) {
                for (int m = 0; m < methods.length; ++m) {
                    methodsJson.put((Object)methods[m]);
                }
            }
            JSONArray rows = this.confidenceLevels.print(resultsGroup, result, methodName, view);
            response.put("settings", (Object)settings);
            response.put("rows", (Object)rows);
            response.put("success", (Object)"ok");
            String string = response.toString();
            return string;
        }
        finally {
            if (locked && resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_ROBTESTSERVLET);
            }
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrintRiskOfRuinStats(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"level", "view"});
        boolean isAlgoWizard = false;
        try {
            isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        ResultsGroup resultsGroup = null;
        boolean locked = false;
        if (isAlgoWizard) {
            resultsGroup = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{SQPaths.algoWizardStrategyPath});
        } else {
            this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy"});
            String _project = parameterMap.get("project")[0].toString();
            String _databank = parameterMap.get("databank")[0].toString();
            String _strategy = parameterMap.get("strategy")[0].toString();
            Databank databank = (Databank)ProjectEngine.get((String)_project).getDatabanks().get((Object)_databank);
            resultsGroup = databank.getLocked(_strategy, LOCK_ROBTESTSERVLET);
            locked = true;
        }
        String methodName = parameterMap.get("methodName")[0].toString();
        String _view = parameterMap.get("view")[0].toString();
        try {
            int _level = Integer.parseInt(parameterMap.get("level")[0]);
            String resultKey = resultsGroup.getMainResultKey();
            Result result = resultsGroup.subResult(resultKey);
            JSONObject response = new JSONObject();
            JSONArray rows = this.riskOfRuins.print(result, methodName, _level, this.rtRRViews.getViewByName(_view));
            response.put("rows", (Object)rows);
            response.put("success", (Object)"ok");
            String string = response.toString();
            return string;
        }
        finally {
            if (locked && resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_ROBTESTSERVLET);
            }
        }
    }
}

