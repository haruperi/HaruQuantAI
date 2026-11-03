/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.lib.memory.SQMemoryProtectionError
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.PlTypes
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.strategy.StrategyLoader
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.lib.memory.SQMemoryProtectionError;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerResultsSender;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSettings;
import com.strategyquant.plugin.Portfolio.impl.Composer.PortfolioComposerSimulator;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.StrategyLoader;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioComposerServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioComposerServlet.class);
    private PortfolioComposerResultsSender sender = new PortfolioComposerResultsSender();
    private StopPauseEngine stopPauseEngine;
    private PortfolioComposerSimulator simulator;
    private ProgressEngine progressEngine;

    public PortfolioComposerServlet() {
        try {
            this.progressEngine = new ProgressEngine("PortfolioComposer");
            this.simulator = new PortfolioComposerSimulator();
            this.stopPauseEngine = new StopPauseEngine();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "recompute": {
                return this.onRecompute(args);
            }
            case "stop": {
                return this.onStop(args);
            }
            case "loadFiles": {
                return this.onLoadFiles(args);
            }
            case "loadGridData": {
                return this.onLoadGridData(args);
            }
            case "removeReports": {
                return this.onRemoveReports(args);
            }
            case "removeAllReports": {
                return this.onRemoveAllReports(args);
            }
            case "addBuyHoldStrategy": {
                return this.onAddBuyHoldStrategy(args);
            }
        }
        return PortfolioComposerServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onAddBuyHoldStrategy(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String symbol = this.tryGetParam(args, "symbol")[0];
        try {
            SQProject project = ProjectEngine.get((String)"PortfolioComposer");
            Databank databank = project.getResultsDatabank();
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
            if (dataInfo == null || dataInfo.symbolInfo == null) {
                throw new TradingException(String.format("Instrument info for symbol '%s doesn't exist", symbol));
            }
            String reportName = "StrBuyHold-" + symbol;
            String path = SQStructure.PLUGINS_DIR + "PortfolioComposer/StrSingleAsset.sqx";
            ResultsGroup rg = StrategyLoader.loadStrategy((SQProject)project, (String)reportName, (String)path, (double)100.0);
            rg.specialValues().set(SpecialValues.PortfolioComposerHodlSymbol, (Object)symbol);
            rg.setName(reportName);
            databank.add(rg, true);
        }
        catch (Exception e) {
            return PortfolioComposerServlet.apiErrorJSON((String)L.t((String)"Adding strategy failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Strategy added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveReports(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String resultsStr = this.tryGetParam(args, "results")[0];
            String[] stgs = resultsStr.split(",");
            SQProject project = ProjectEngine.get((String)"PortfolioComposer");
            Databank databank = project.getResultsDatabank();
            ProjectConfigHelper.delete((SQProject)project, (Databank)databank, (String[])stgs, (String)"onRemoveReports");
            databank.addExtraDatabankChange("remove", "DatabankEmpty");
        }
        catch (Exception e) {
            return PortfolioComposerServlet.apiErrorJSON((String)L.t((String)"Removing reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Reports removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveAllReports(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            SQProject project = ProjectEngine.get((String)"PortfolioComposer");
            Databank databank = project.getResultsDatabank();
            databank.removeAll(true, String.format("API request portfoliocomposer/removeAllReports from databank %s/%s", project.getName(), databank.getName()));
            databank.addExtraDatabankChange("remove", "DatabankEmpty");
        }
        catch (Exception e) {
            return PortfolioComposerServlet.apiErrorJSON((String)L.t((String)"Removing reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Reports removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadGridData(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray rows = new JSONArray();
        SQProject project = ProjectEngine.get((String)"PortfolioComposer");
        Databank databank = project.getResultsDatabank();
        JSONArray mmMethods = new JSONArray();
        HashSet<String> mmMethodsSet = new HashSet<String>();
        boolean mmMethodsDifferent = false;
        ArrayList strategies = databank.getRecords();
        for (int i = 0; i < strategies.size(); ++i) {
            ResultsGroup rg = (ResultsGroup)strategies.get(i);
            String name = rg.getName();
            try {
                MoneyManagementMethod mmMethod = ProjectConfigHelper.getMoneyManagement((Element)XMLUtil.stringToElement((String)rg.getLastSettings()).getChild("RiskMoneyManagement").getChild("MoneyManagement"));
                String mm = mmMethod.printFormatedName();
                if (!mmMethodsSet.isEmpty() && !mmMethodsSet.contains(mm)) {
                    mmMethodsDifferent = true;
                }
                mmMethodsSet.add(mm);
                double initialCapital = mmMethod.getInitialCapital();
                mmMethods.put((Object)(name + " - " + mm + " / " + PlTypes.printPL((double)initialCapital, (byte)10)));
            }
            catch (Exception e) {
                Log.error(String.format("Error while parsing the MoneyManagement method used for strategy %s", name), (Throwable)e);
                mmMethods.put((Object)(name + " - NA"));
            }
            DatabankColumn miniEquityChart = (DatabankColumn)DatabankColumns.get().findClassByName("MiniEquityChart");
            String miniEquityChartValue = miniEquityChart.getValue(rg, "Portfolio", (byte)0, (byte)10, (byte)127);
            JSONArray rowData = new JSONArray();
            rowData.put((Object)rg.getName());
            rowData.put((Object)miniEquityChartValue);
            rows.put((Object)rowData);
        }
        response.put("mmMethods", (Object)mmMethods);
        response.put("mmMethodsDifferent", mmMethodsDifferent);
        response.put("rows", (Object)rows);
        response.put("success", (Object)L.t((String)"Data loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onRecompute(Map<String, String[]> args) throws Exception {
        SQProject project;
        String resultsStr = this.tryGetParam(args, "results")[0];
        String weightsStr = this.tryGetParam(args, "weights")[0];
        String[] results = resultsStr.split(",");
        String[] weights = weightsStr.split(",");
        final PortfolioComposerSettings settings = new PortfolioComposerSettings();
        settings.dateRangeLimited = this.tryGetParam(args, "dateRange")[0].equals("limited");
        settings.startDay = SQTime.parseDateToMilis((String)this.tryGetParam(args, "startDay")[0]);
        settings.endDay = SQTime.parseDateToMilis((String)this.tryGetParam(args, "endDay")[0]);
        settings.initialCapital = Double.valueOf(this.tryGetParam(args, "initialCapital")[0]);
        settings.leverage = Integer.valueOf(this.tryGetParam(args, "leverage")[0]);
        settings.decimals = 5;
        final boolean autocomputation = this.tryGetParam(args, "autocomputation")[0].equals("true");
        if (autocomputation) {
            String selectionType = this.getParam(args, "selectionType", "SharpRatio");
            settings.setSelectionTypeByString(selectionType);
            settings.maxSimulations = Integer.parseInt(args.get("maxSimulations")[0]);
            int confLevel = Integer.parseInt(args.get("confLevel")[0]);
            settings.confidenceLevel = Double.valueOf(confLevel) / 100.0;
            settings.RiskFreeRate = Double.parseDouble(args.get("riskFreeRate")[0]);
        }
        if (results.length != weights.length) {
            throw new Exception("The lengths of the results / weights arrays do not match.");
        }
        if (results.length > 50) {
            throw new Exception("Select max 50 strategies to create a portfolio.");
        }
        if (this.stopPauseEngine.getRunningStatus() == 1) {
            throw new Exception(L.t((String)"Computing Portfolio is already running. Cannot start another process.", (Object[])new Object[0]));
        }
        if (!MainApp.getLicenseInfo().isUltimateEdition() && results.length > 4) {
            throw new Exception(L.t((String)"Portfolio Composer in Pro version is limited to maximum 4 source strategies.", (Object[])new Object[0]));
        }
        if (MainApp.getLicenseInfo().isActiveSpecialTrial()) {
            throw new Exception(L.t((String)"PortfolioComposer is available only in full version, not in this special trial.", (Object[])new Object[0]));
        }
        try {
            project = ProjectEngine.get((String)"PortfolioComposer");
            Databank databankInput = (Databank)project.getDatabanks().get((Object)"Results");
            for (int i = 0; i < results.length; ++i) {
                String strategy = results[i];
                double weight = Double.valueOf(weights[i]);
                ResultsGroup rg = databankInput.getLocked(strategy, "PortfolioComposer");
                settings.strategies.add(rg);
                settings.weights.add(weight);
            }
        }
        catch (Throwable throwable) {
            for (ResultsGroup rg : settings.strategies) {
                rg.releaseLock("PortfolioComposer");
            }
            throw throwable;
        }
        for (ResultsGroup rg : settings.strategies) {
            rg.releaseLock("PortfolioComposer");
        }
        new Thread(this){
            final /* synthetic */ PortfolioComposerServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.simulator.start(project, settings, this.this$0.sender, this.this$0.stopPauseEngine, autocomputation);
            }
        }.start();
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onLoadFiles(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        final String[] paths = this.tryGetParam(args, "filePaths[]");
        new Thread(this){
            final /* synthetic */ PortfolioComposerServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.loadFiles(paths);
                Log.info("Strategies loaded");
            }
        }.start();
        response.put("success", (Object)L.t((String)"Loading strategies.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void loadFiles(String[] paths) {
        Throwable lastException = null;
        SQProject project = null;
        Databank databank = null;
        try {
            project = ProjectEngine.get((String)"PortfolioComposer");
            databank = project.getResultsDatabank();
            project.bestResults.disable();
            databank.disableSynchronization();
            project.publisher.resetLastData("progress-channel");
            String reportName = null;
            boolean dontStop = false;
            double progress = 0.0;
            double step = 100.0 / (double)paths.length;
            StrategyLoader.init();
            for (int i = 0; i < paths.length; ++i) {
                try {
                    File f = new File(paths[i]);
                    if (f.isDirectory()) continue;
                    if (!SQProject.isMemoryProtectionUsed() && !dontStop) {
                        try {
                            MemoryUsageChecker.checkAvailableMemory();
                        }
                        catch (SQMemoryProtectionError e) {
                            project.userConfirm.awaitConfirmation(L.t((String)"Memory usage warning", (Object[])new Object[0]), L.t((String)"SQ is running out of memory - current consumption reached 85%.", (Object[])new Object[0]) + "<br>" + L.t((String)"If you'll continue, SQ might crash or freeze when memory runs out.", (Object[])new Object[0]) + "<br>" + L.t((String)"We recommend you to stop further strategies loading and eventually to increase available memory in performance settings.", (Object[])new Object[0]) + "<br><br>" + L.t((String)"Do you want to stop loading remaining strategies?", (Object[])new Object[0]));
                            if (project.userConfirm.isConfirmed()) {
                                break;
                            }
                            dontStop = true;
                        }
                    }
                    reportName = SQUtils.stripExtension((String)f.getName());
                    ResultsGroup resultsGroup = StrategyLoader.loadStrategy((SQProject)project, (String)reportName, (String)paths[i], (double)progress);
                    progress += step;
                    if (resultsGroup != null) {
                        databank.add(resultsGroup, true);
                        continue;
                    }
                    break;
                }
                catch (Exception e) {
                    Log.error("Error while loading strategies. Exc.", (Throwable)e);
                    lastException = e;
                    continue;
                }
                catch (Error e) {
                    Log.error("Error while loading strategies. Exc.", (Throwable)e);
                    lastException = e;
                    break;
                }
            }
        }
        catch (Exception ex) {
            Log.error("Error while loading strategies. Exc.", (Throwable)ex);
            lastException = ex;
        }
        finally {
            databank.enableSynchronization();
        }
        project.bestResults.enable();
        if (!StrategyLoader.isCanceled()) {
            project.getProgress().update("load", 100.0, lastException == null ? null : "Some strategies were not loaded because of errors.<br>Last error: " + lastException.getMessage());
        }
    }

    private String onStop(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        this.stopPauseEngine.stop();
        System.gc();
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

