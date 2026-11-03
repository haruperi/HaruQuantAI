/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.tradinglib.CustomCellFormat
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.WalkForwardColumn
 *  com.strategyquant.tradinglib.WalkForwardPeriod
 *  com.strategyquant.tradinglib.WalkForwardResult
 *  com.strategyquant.tradinglib.conditions.Condition
 *  com.strategyquant.tradinglib.conditions.IConditionValue
 *  com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DatabankTableView
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.optimization.WalkForwardColumns
 *  com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult
 *  com.strategyquant.tradinglib.optimization.WalkForwardParametersStability
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.WalkForward;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.plugin.Results.impl.WalkForward.WFParamsExport;
import com.strategyquant.plugin.Results.impl.WalkForward.views.WFViews;
import com.strategyquant.tradinglib.CustomCellFormat;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.WalkForwardColumn;
import com.strategyquant.tradinglib.WalkForwardPeriod;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.conditions.Condition;
import com.strategyquant.tradinglib.conditions.IConditionValue;
import com.strategyquant.tradinglib.crosscheck.CrossCheckDataNotExistException;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DatabankTableView;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.optimization.WalkForwardColumns;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.optimization.WalkForwardParametersStability;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkForwardServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(WalkForwardServlet.class);
    private static final String LOCK_WFSERVLET = "WalkForwardServlet";
    private static IResultsGroupProvider rgProvider;
    private WFViews views;

    public WalkForwardServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
        this.views = new WFViews(MainApp.getDataPath() + "/user/settings/views/walkForwardResults");
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        if (command.startsWith("views")) {
            return this.views.execute(command, parameterMap, method);
        }
        switch (command) {
            case "getConditions": {
                return this.onGetConditions(parameterMap);
            }
            case "print": {
                return this.onPrint(parameterMap);
            }
            case "printTable": {
                return this.onPrintTable(parameterMap);
            }
            case "printCellConditions": {
                return this.onPrintCellConditions(parameterMap);
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
    private String onExport(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"path", "useComma"});
        String _project = parameterMap.get("project")[0].toString();
        String _databank = parameterMap.get("databank")[0].toString();
        String _strategy = parameterMap.get("strategy")[0].toString();
        String _resultkey = parameterMap.get("resultkey")[0].toString();
        String viewName = parameterMap.get("view")[0].toString();
        String path = parameterMap.get("path")[0];
        boolean useComma = Boolean.parseBoolean(parameterMap.get("useComma")[0]);
        JSONObject response = new JSONObject();
        Databank databank = (Databank)ProjectEngine.get((String)_project).getDatabanks().get((Object)_databank);
        ResultsGroup resultsGroup = databank.getLocked(_strategy, LOCK_WFSERVLET);
        try {
            DatabankTableView view = this.views.getViewByName(viewName);
            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (mwfResult == null) {
                throw new Exception("WF results not found.");
            }
            WalkForwardResult wfResult = mwfResult.getWFResult(_resultkey, false);
            WFParamsExport export = new WFParamsExport();
            if (path.endsWith("xlsx")) {
                export.toXlsx(path, useComma, wfResult, view);
            } else {
                export.toCsv(path, useComma, wfResult, view);
            }
        }
        catch (Exception e) {
            String string = WalkForwardServlet.apiErrorJSON((String)L.t((String)"WF params export failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            resultsGroup.releaseLock(LOCK_WFSERVLET);
        }
        JSONObject responseJSON = new JSONObject();
        responseJSON.put("success", (Object)"WF params exported.");
        return responseJSON.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized String onGetConditions(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String conditions = "<Conditions/>";
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_WFSERVLET);
            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (mwfResult == null) {
                throw new Exception("WalkForwardResult not found.");
            }
            if (mwfResult.conditionsElem == null) {
                mwfResult.conditionsElem = (Element)resultsGroup.specialValues().get("WalkForwardConditions");
            }
            if (mwfResult.conditionsElem == null) {
                throw new Exception("Conditions not found.");
            }
            conditions = XMLUtil.elementToString((Element)mwfResult.conditionsElem);
        }
        catch (RecordNotFoundException e) {
            Log.info("onGetConditions: " + e.getMessage());
            String string = WalkForwardServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            Log.error("Error while loading WF Conditions. Exc.", (Throwable)e);
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_WFSERVLET);
            }
        }
        response.put("conditions", (Object)conditions);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy", "resultkey", "conditions", "thresholdPct"});
        String _resultkey = parameterMap.get("resultkey")[0].toString();
        String _conditions = parameterMap.get("conditions")[0].toString();
        int _thresholdPct = Integer.parseInt(parameterMap.get("thresholdPct")[0]);
        int _robRows = Integer.parseInt(parameterMap.get("robRows")[0]);
        int _robColumns = Integer.parseInt(parameterMap.get("robColumns")[0]);
        int _robComb = Integer.parseInt(parameterMap.get("robComb")[0]);
        String _type = parameterMap.get("type")[0].toString();
        Element elColumn = null;
        if (parameterMap.containsKey("column")) {
            try {
                elColumn = XMLUtil.stringToXmlElement((String)parameterMap.get("column")[0].toString());
            }
            catch (Exception e) {
                Log.error("Exc.", (Throwable)e);
            }
        }
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_WFSERVLET);
            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (mwfResult != null) {
                WalkForwardResult wfResult = mwfResult.getWFResult(_resultkey, false);
                Element conditionsEl = this.getConditionsEl(mwfResult, _conditions, _thresholdPct, _robRows, _robColumns, _robComb);
                ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
                if (this.paramsChanged(mwfResult, conditions, _thresholdPct, _robRows, _robColumns, _robComb)) {
                    mwfResult.computeRobustnessResults(resultsGroup, conditionsEl, conditions, _thresholdPct, _robRows, _robColumns, _robComb);
                }
                response.put("chart", (Object)this.printChart(resultsGroup, mwfResult, elColumn, _type));
                response.put("conditions", (Object)this.printConditionsTable(resultsGroup, wfResult, conditionsEl, conditions));
                response.put("result", (Object)this.printRobustnessResult(mwfResult, _resultkey, _robRows * _robColumns));
            }
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = WalkForwardServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = WalkForwardServlet.apiErrorJSON((String)L.t((String)"Getting walk forward results failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_WFSERVLET);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private Element getConditionsEl(WalkForwardMatrixResult mwfResult, String _conditions, int thresholdPct, int rows, int cols, int robComb) {
        Element conditionsEl = null;
        try {
            if (_conditions.equals("replace-default-conditions") || _conditions.equals("add-default-conditions")) {
                if (_conditions.equals("replace-default-conditions") || mwfResult.conditionsElem == null) {
                    conditionsEl = XMLUtil.fileToXmlElement((File)new File(SQPaths.wfDefaultConditionsPath));
                } else {
                    conditionsEl = mwfResult.conditionsElem.clone();
                    Element defConditionsEl = XMLUtil.fileToXmlElement((File)new File(SQPaths.wfDefaultConditionsPath));
                    for (Element conditionEl : defConditionsEl.getChildren("Condition")) {
                        conditionsEl.addContent((Content)conditionEl.clone());
                    }
                }
                conditionsEl.setAttribute("thresholdPct", "80");
                conditionsEl.setAttribute("robCombRows", "3");
                conditionsEl.setAttribute("robCombCols", "3");
                conditionsEl.setAttribute("robMinComb", "7");
            } else {
                conditionsEl = XMLUtil.stringToElement((String)_conditions);
                conditionsEl.setAttribute("thresholdPct", thresholdPct + "");
                conditionsEl.setAttribute("robCombRows", rows + "");
                conditionsEl.setAttribute("robCombCols", cols + "");
                conditionsEl.setAttribute("robMinComb", robComb + "");
            }
        }
        catch (Exception e) {
            Log.error("Cannot parse conditions. Exc.", (Throwable)e);
        }
        return conditionsEl;
    }

    private boolean paramsChanged(WalkForwardMatrixResult mwfResult, ArrayList<Condition> conditions, int thresholdPct, int robRows, int robColumns, int robComb) {
        if (mwfResult.conditions == null || mwfResult.conditions.size() != conditions.size() || mwfResult.thresholdPct != thresholdPct || mwfResult.rows != robRows || mwfResult.cols != robColumns || mwfResult.comb != robComb) {
            return true;
        }
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition1 = (Condition)mwfResult.conditions.get(i);
            Condition condition2 = conditions.get(i);
            if (condition1.toString().equals(condition2.toString()) && condition1.isUsed() == condition2.isUsed()) continue;
            return true;
        }
        return false;
    }

    private JSONObject printRobustnessResult(WalkForwardMatrixResult mwfResult, String resultkey, int groupSize) throws Exception {
        boolean runPassed;
        boolean passed;
        WalkForwardResult wfResult = null;
        if (mwfResult.getResultList().size() > 1) {
            wfResult = mwfResult.getWFResult(resultkey, false);
            passed = mwfResult.passed;
            runPassed = wfResult.passed;
        } else {
            wfResult = (WalkForwardResult)mwfResult.getResultList().get(0);
            passed = wfResult.passed;
            runPassed = wfResult.passed;
        }
        JSONObject data = new JSONObject();
        data.put("combination", (Object)wfResult.toString(mwfResult.periodType));
        data.put("matrixResult", mwfResult.getResultList().size() > 1);
        data.put("passed", passed);
        data.put("runPassed", runPassed);
        data.put("condPassed", wfResult.passedConditions);
        data.put("condTotal", wfResult.testedConditions);
        data.put("combPassed", mwfResult.combinationsPassed);
        data.put("combTotal", mwfResult.combinationsTotal);
        data.put("condPassedInBestGroup", mwfResult.condPassedInBestGroup);
        data.put("groupSize", groupSize);
        data.put("bestGroupArroundCell", (Object)mwfResult.bestGroupArroundCell);
        data.put("recommendedCombination", (Object)mwfResult.recommendedCombination);
        data.put("scorePct", wfResult.scorePerc);
        return data;
    }

    private String printConditionsTable(ResultsGroup resultsGroup, WalkForwardResult wfResult, Element conditionsEl, ArrayList<Condition> conditions) throws Exception {
        for (int i = 0; i < conditions.size(); ++i) {
            Condition condition = conditions.get(i);
            try {
                boolean met = condition.isMet(new Object[]{resultsGroup, wfResult});
                Element conditionEl = (Element)conditionsEl.getChildren().get(i);
                conditionEl.setAttribute("passed", met + "");
                Element leftSideElem = conditionEl.getChild("Left-Side");
                try {
                    ((Element)leftSideElem.getChildren().get(0)).setAttribute("value", condition.getLeftStatsValue() + "");
                }
                catch (Exception exception) {
                    // empty catch block
                }
                Element rightSideElem = conditionEl.getChild("Right-Side");
                try {
                    ((Element)rightSideElem.getChildren().get(0)).setAttribute("value", condition.getRightStatsValue() + "");
                }
                catch (Exception exception) {}
                continue;
            }
            catch (Exception e) {
                Log.error("Error while checking condition", (Throwable)e);
            }
        }
        return XMLUtil.elementToString((Element)conditionsEl);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized String onPrintCellConditions(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy", "conditions", "thresholdPct", "cellX", "cellY"});
        String _conditions = parameterMap.get("conditions")[0].toString();
        int _thresholdPct = Integer.parseInt(parameterMap.get("thresholdPct")[0]);
        int cellX = Integer.parseInt(parameterMap.get("cellX")[0]);
        int cellY = Integer.parseInt(parameterMap.get("cellY")[0]);
        int _robRows = parameterMap.containsKey("robRows") ? Integer.parseInt(parameterMap.get("robRows")[0]) : 3;
        int _robColumns = parameterMap.containsKey("robColumns") ? Integer.parseInt(parameterMap.get("robColumns")[0]) : 3;
        int _robComb = parameterMap.containsKey("robComb") ? Integer.parseInt(parameterMap.get("robComb")[0]) : 7;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_WFSERVLET);
            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (mwfResult == null) {
                throw new Exception("WalkForwardResult not found.");
            }
            WalkForwardResult wfResult = mwfResult.getWFResult(cellX, cellY);
            if (wfResult == null) {
                throw new Exception("WalkForwardResult not found for cell (" + cellX + ", " + cellY + ").");
            }
            Element conditionsEl = this.getConditionsEl(mwfResult, _conditions, _thresholdPct, _robRows, _robColumns, _robComb);
            ArrayList conditions = ProjectConfigHelper.getConditions((Element)conditionsEl);
            String conditionsXml = this.printConditionsTable(resultsGroup, wfResult, conditionsEl, conditions);
            response.put("conditions", (Object)conditionsXml);
            response.put("cellX", cellX);
            response.put("cellY", cellY);
            response.put("scorePerc", wfResult.scorePerc);
            response.put("passed", wfResult.passed);
            response.put("combination", (Object)wfResult.toString(mwfResult.periodType));
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrintCellConditions: " + e.getMessage());
            String string = WalkForwardServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = WalkForwardServlet.apiErrorJSON((String)L.t((String)"Getting cell conditions failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_WFSERVLET);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONObject printChart(ResultsGroup resultsGroup, WalkForwardMatrixResult mwfResult, Element elColumn, String type) throws Exception {
        if (mwfResult == null || mwfResult.getResultList().size() == 1 || elColumn == null) {
            return null;
        }
        JSONObject data = new JSONObject();
        double min = -1.0;
        double max = -1.0;
        JSONArray values = new JSONArray();
        IConditionValue conditionValue = ProjectConfigHelper.getConditionValue((Element)elColumn);
        if (type.equals("score")) {
            JSONArray x = new JSONArray();
            for (int j = mwfResult.start1; j <= mwfResult.stop1; j += mwfResult.increment1) {
                x.put(j);
            }
            data.put("x", (Object)x);
            JSONArray y = new JSONArray();
            for (int i = mwfResult.start2; i <= mwfResult.stop2; i += mwfResult.increment2) {
                y.put(i);
            }
            data.put("y", (Object)y);
            for (int j = mwfResult.start2; j <= mwfResult.stop2; j += mwfResult.increment2) {
                JSONArray row = new JSONArray();
                for (int i = mwfResult.start1; i <= mwfResult.stop1; i += mwfResult.increment1) {
                    WalkForwardResult wfResult2 = mwfResult.getWFResult(i, j);
                    boolean bestResult = wfResult2.toString(mwfResult.periodType).equals(mwfResult.bestGroupArroundWFCell.toString(mwfResult.periodType)) && mwfResult.passed;
                    row.put((Object)new JSONArray().put(wfResult2.passed).put(wfResult2.scorePerc).put(bestResult));
                }
                values.put((Object)row);
            }
        } else {
            for (int j = mwfResult.start2; j <= mwfResult.stop2; j += mwfResult.increment2) {
                for (int i = mwfResult.start1; i <= mwfResult.stop1; i += mwfResult.increment1) {
                    WalkForwardResult wfResult = mwfResult.getWFResult(i, j);
                    double value = 0.0;
                    try {
                        value = conditionValue.getValue(new Object[]{resultsGroup, wfResult});
                    }
                    catch (CrossCheckDataNotExistException wfResult2) {
                    }
                    catch (Exception e) {
                        Log.error("Exc.", (Throwable)e);
                    }
                    if (min == -1.0 && max == -1.0) {
                        min = value;
                        max = value;
                    }
                    if (value < min) {
                        min = value;
                    }
                    if (value > max) {
                        max = value;
                    }
                    values.put((Object)new JSONObject().put("x", i).put("y", j).put("z", value).put("style", value));
                }
            }
        }
        data.put("values", (Object)values);
        int valueType = 1;
        String valueLabel = L.t((String)"Value", (Object[])new Object[0]);
        try {
            DatabankColumn column;
            String columnName = elColumn.getAttributeValue("class");
            if (DatabankColumns.get().checkClassExists(columnName)) {
                column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
                valueType = column.getValueType();
                valueLabel = conditionValue.getTitle();
            } else if (WalkForwardColumns.get().checkClassExists(columnName)) {
                column = (WalkForwardColumn)WalkForwardColumns.get().findClassByName(columnName);
                valueType = column.getValueType();
                valueLabel = conditionValue.getTitle();
            }
            if (columnName.equals("WFScore")) {
                data.put("zMin", 0);
                data.put("zMax", 100);
            }
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
        }
        if (!data.has("zMin")) {
            data.put("zMin", min);
            data.put("zMax", max);
        }
        data.put("reverseColorScale", valueType == 2);
        data.put("reverseColorScale", valueType == 2);
        data.put("periodInPercent", mwfResult.periodType == 10);
        data.put("xlabel", (Object)(mwfResult.periodType == 10 ? L.t((String)"OOS %", (Object[])new Object[0]) : L.t((String)"IS days", (Object[])new Object[0])));
        data.put("ylabel", (Object)(mwfResult.periodType == 10 ? L.t((String)"Runs", (Object[])new Object[0]) : L.t((String)"OOS days", (Object[])new Object[0])));
        data.put("zlabel", (Object)valueLabel);
        return data;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized String onPrintTable(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy", "resultkey"});
        String _resultkey = parameterMap.get("resultkey")[0].toString();
        String viewName = parameterMap.get("view")[0].toString();
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = rgProvider.get(parameterMap, LOCK_WFSERVLET);
        try {
            DatabankTableView view = this.views.getViewByName(viewName);
            MainApp.settings().set("wfResultsView", viewName);
            response.put("rows", (Object)new JSONArray());
            response.put("success", (Object)"ok");
            WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
            if (mwfResult != null) {
                WalkForwardResult wfResult = mwfResult.getWFResult(_resultkey, false);
                response.put("rows", (Object)this.printTable(wfResult, view));
                response.put("combination", (Object)wfResult.toString(mwfResult.periodType));
                response.put("matrixResult", mwfResult.getResultList().size() > 1);
                try {
                    double stability = (Double)resultsGroup.specialValues().get(WalkForwardParametersStability.getSpecialValuesKey((String)_resultkey));
                    response.put("parametersStability", stability);
                }
                catch (Exception e) {
                    Log.error("Cannot get parameters stability for result '" + _resultkey + "'", (Throwable)e);
                    response.put("parametersStability", (Object)"N/A");
                }
            }
            String string = response.toString();
            return string;
        }
        finally {
            resultsGroup.releaseLock(LOCK_WFSERVLET);
        }
    }

    private JSONArray printTable(WalkForwardResult wfResult, DatabankTableView view) {
        JSONArray rows = new JSONArray();
        ArrayList periods = wfResult.wfPeriods;
        for (int i = 0; i < periods.size(); ++i) {
            WalkForwardPeriod period = (WalkForwardPeriod)periods.get(i);
            JSONObject row = new JSONObject();
            JSONArray rowData = new JSONArray();
            rowData.put((Object)(SQTime.toDateString((long)period.optimizeFrom) + " - " + SQTime.toDateString((long)period.optimizeTo)));
            if (i == periods.size() - 1) {
                rowData.put((Object)(SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo) + " (future)"));
            } else {
                rowData.put((Object)(SQTime.toDateString((long)period.runFrom) + " - " + SQTime.toDateString((long)period.runTo)));
            }
            rowData.put(SQTime.getDaysBetween((long)period.optimizeFrom, (long)period.optimizeTo));
            rowData.put(SQTime.getDaysBetween((long)period.runFrom, (long)period.runTo));
            ArrayList columns = view.columns;
            for (int columnIndex = 0; columnIndex < columns.size(); ++columnIndex) {
                DatabankTableColumnEntry columnEntry = (DatabankTableColumnEntry)columns.get(columnIndex);
                DatabankColumn column = columnEntry.tableColumn;
                try {
                    rowData.put(columnEntry.sampleType == 10 ? column.getNumericValue(period.optimizationStatData) : column.getNumericValue(period.runStatData));
                    continue;
                }
                catch (Exception e) {
                    Log.error("WF column value couldn't be printed.", (Throwable)e);
                    rowData.put((Object)"N/A");
                }
            }
            rowData.put((Object)period.testParameters);
            row.put("id", (Object)("r" + i));
            if (i == periods.size() - 1) {
                row.put("class", (Object)"wf-italic");
            }
            row.put("data", (Object)rowData);
            rows.put((Object)row);
        }
        return rows;
    }

    public String printHtmlFormatedValue(SQStats stats, DatabankColumn column, String customStyle) throws Exception {
        double value = column.getNumericValue(stats);
        CustomCellFormat cellFormat = column.getCustomFormat((byte)0, (byte)10, (byte)127, Double.toString(value), null);
        cellFormat.customStyle = customStyle;
        return cellFormat.getHtmlContent((Object)value);
    }
}

