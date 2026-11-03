/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.Variable
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.optimization.OptimizationSettings
 *  com.strategyquant.tradinglib.optimization.Parameter
 *  com.strategyquant.tradinglib.optimization.ParametersSettings
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectCustomResources
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.strategy.StrategyLoader
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Optimization;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.optimization.OptimizationSettings;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectCustomResources;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.strategy.StrategyLoader;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OptimizationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(OptimizationServlet.class);
    private static final String LOCK_OPTSERVLET = "OptimizationServlet";
    private static OptimizationServlet instance;

    public OptimizationServlet() {
        instance = this;
    }

    public static OptimizationServlet getInstance() {
        return instance;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "loadStrategyToOptimize": {
                return this.onLoadStrategyToOptimize(args);
            }
            case "loadStrategy": {
                return this.onLoadStrategy(args);
            }
            case "getNumberOfTests": {
                return this.onGetNumberOfTests(args);
            }
        }
        return OptimizationServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onLoadStrategyToOptimize(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        SQProject project = null;
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String taskName = this.tryGetParam(args, "taskName")[0];
            String filePath = this.tryGetParam(args, "filePath")[0];
            String clearResultsStr = this.tryGetParam(args, "clearResults")[0];
            boolean clearResults = clearResultsStr.equals("true");
            String strategyFileName = new File(filePath).getName();
            project = ProjectEngine.get((String)projectName);
            Databank databank = ProjectConfigHelper.getOutputDatabank((String)projectName, (String)taskName);
            ResultsGroup strategy = null;
            StrategyLoader.init();
            strategy = StrategyLoader.loadStrategy((SQProject)project, (String)strategyFileName, (String)filePath, (double)99.0);
            if (strategy == null) {
                throw new Exception(L.t((String)"Error while loading.", (Object[])new Object[0]));
            }
            project.getProgress().update("load", 100.0, null);
            for (String strategyName : databank.getRecordKeys()) {
                if (!clearResults && !strategyName.equals(strategy.getName())) continue;
                databank.remove(strategyName, true, true, false, true, LOCK_OPTSERVLET);
            }
            databank.add(strategy, true);
            databank.updateBestResults(strategy);
            if (strategy.getLastSettings() != null) {
                response.put("lastSettingsXml", (Object)strategy.getLastSettings());
            }
        }
        catch (Exception e) {
            Log.error("Cannot load strategy. ", (Throwable)e);
            if (project != null) {
                project.getProgress().update("load", 100.0, e.getMessage());
            }
            return OptimizationServlet.apiErrorJSON((String)L.t((String)"Cannot load strategy.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Report(s) loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onLoadStrategy(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        SQProject project = null;
        String filePath = null;
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String taskName = this.tryGetParam(args, "taskName")[0];
            filePath = this.tryGetParam(args, "filePath")[0];
            String symmetricVariables = this.tryGetParam(args, "symmetricVariables")[0];
            boolean symmetric = symmetricVariables.equals("true");
            project = ProjectEngine.get((String)projectName);
            Element settingsElem = project.getTaskSettingsByName(taskName);
            Databank databank = ProjectConfigHelper.getOutputDatabank((String)projectName, (Element)settingsElem);
            String strategyFileName = new File(filePath).getName();
            String strategyName = SQUtils.stripExtension((String)strategyFileName);
            Element elStrategy = null;
            ResultsGroup strategy = null;
            try {
                strategy = databank.getLocked(strategyName, LOCK_OPTSERVLET);
                elStrategy = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)strategy);
            }
            catch (Exception e) {
                StrategyLoader.init();
                strategy = StrategyLoader.loadStrategy((SQProject)project, (String)strategyName, (String)filePath, (double)99.0);
                if (strategy == null) {
                    throw new Exception(L.t((String)"Strategy not loaded.", (Object[])new Object[0]));
                }
                project.getProgress().update("load", 100.0, null);
                if (databank.isLoaded()) {
                    databank.add(strategy, true);
                    databank.updateBestResults(strategy);
                }
                elStrategy = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)strategy);
            }
            finally {
                if (strategy != null) {
                    strategy.releaseLock(LOCK_OPTSERVLET);
                }
            }
            if (elStrategy != null) {
                this.changeSymmetry(settingsElem, elStrategy, symmetric, response);
            }
            Element elResources = ProjectCustomResources.checkStrategyResources((Element)elStrategy);
            response.put("xmlConfig", (Object)XMLUtil.elementToString((Element)elStrategy));
            response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)elResources));
        }
        catch (Exception e) {
            if (project != null) {
                if (filePath != null) {
                    project.getProgress().update("load", 100.0, L.t((String)"Failed to load strategy parameters from file '%s', file does not exist?!", (Object[])new Object[]{filePath}));
                } else {
                    project.getProgress().update("load", 100.0, L.t((String)"Failed to load strategy parameters, file does not exist?!", (Object[])new Object[0]));
                }
            }
            return OptimizationServlet.apiErrorJSON((String)L.t((String)"Cannot get strategy's variables.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Variables returned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetNumberOfTests(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String databankName = this.tryGetParam(args, "databankName")[0];
            String taskConfig = this.tryGetParam(args, "taskConfig")[0];
            Element elSettings = XMLUtil.stringToElement((String)taskConfig);
            long paramsCombinations = 0L;
            try {
                OptimizationSettings optimizationSettings = new OptimizationSettings(projectName);
                Element elOptimization = elSettings.getChild("Optimization");
                if (elOptimization == null) {
                    response.put("success", (Object)L.t((String)"Number of tests returned.", (Object[])new Object[0]));
                    response.put("numberOfTests", (Object)"N/A");
                    return response.toString();
                }
                optimizationSettings.setFromXML(elSettings, elOptimization);
                if (!optimizationSettings.singleStrategy) {
                    response.put("success", (Object)L.t((String)"Number of tests returned.", (Object[])new Object[0]));
                    response.put("numberOfTests", (Object)"N/A");
                    return response.toString();
                }
                paramsCombinations = this.getSingleStrategyCombinations(optimizationSettings.strategyFile, elSettings);
                response.put("settingsXML", (Object)XMLUtil.elementToString((Element)elSettings));
                response.put("numberOfTests", paramsCombinations >= 0L ? Long.valueOf(paramsCombinations) : "More than 2^64");
            }
            catch (Exception e) {
                Log.error("Cannot get number of tests. ", (Throwable)e);
                response.put("numberOfTests", (Object)"N/A");
            }
        }
        catch (Exception e) {
            Log.error("Cannot get number of tests. ", (Throwable)e);
            return OptimizationServlet.apiErrorJSON((String)L.t((String)"Cannot get number of tests.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Number of tests returned.", (Object[])new Object[0]));
        return response.toString();
    }

    private long getSingleStrategyCombinations(File strategyFile, Element elSettings) throws Exception {
        ResultsGroup rg = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{strategyFile.getAbsolutePath()});
        return this.getCombinationsCount(rg, elSettings);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private long getAllStrategiesCombinations(String projectName, String databankName, Element taskConfig) throws Exception {
        Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
        Element elSettings = taskConfig.getChild("Settings");
        long combinations = 0L;
        if (databank.size() == 0) {
            return 0L;
        }
        ArrayList recordKeys = databank.getRecordKeys();
        for (int a = 0; a < recordKeys.size(); ++a) {
            ResultsGroup rg = null;
            try {
                rg = databank.getLocked((String)recordKeys.get(a), LOCK_OPTSERVLET);
                combinations = Math.addExact(combinations, this.getCombinationsCount(rg, elSettings));
                if (combinations >= 0L) continue;
                long l = -1L;
                return l;
            }
            catch (ArithmeticException e) {
                long l = -1L;
                return l;
            }
            catch (Exception e) {
                continue;
            }
            finally {
                if (rg != null) {
                    rg.releaseLock(LOCK_OPTSERVLET);
                }
            }
        }
        return combinations;
    }

    private long getCombinationsCount(ResultsGroup rg, Element elSettings) throws Exception {
        ParametersSettings paramSettings = new ParametersSettings();
        paramSettings.setFromXML(elSettings, rg.getStrategyXml());
        return paramSettings.combinationsCount;
    }

    private void changeSymmetry(Element settingsElem, Element elStrategy, boolean symmetric, JSONObject response) throws Exception {
        if (elStrategy == null) {
            throw new Exception(L.t((String)"Record doesn't contain any editable strategy.", (Object[])new Object[0]));
        }
        ParametersSettings paramSettings = new ParametersSettings();
        paramSettings.setFromXML(settingsElem, elStrategy);
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)elStrategy.clone().detach());
        xmlS.transformToVariables(symmetric && xmlS.isSymmetryEnabled(), paramSettings.paramTypes);
        Variables vars = xmlS.variables();
        if (this.shouldSort(vars)) {
            vars.sortByName();
        }
        boolean isStockpickerStrategy = false;
        try {
            isStockpickerStrategy = elStrategy.getChild("Strategy").getAttributeValue("pickerEditor").equals("true");
        }
        catch (Exception exception) {
            // empty catch block
        }
        JSONArray variables = new JSONArray();
        for (int a = 0; a < vars.size(); ++a) {
            Variable var = (Variable)vars.get(a);
            if (!var.isAutoGenerated() && !var.isMakeExternal()) continue;
            String id = var.getId();
            String paramType = var.getParamType();
            byte type = var.getInternalType();
            String name = var.getName();
            String value = var.getValue();
            if (type == 3 || name.contains("EntrySignal") || name.contains("ExitSignal") || name.contains("ReplaceExistingOrders") || type == 0 || name.startsWith("Magic") || isStockpickerStrategy && paramType != null && paramType.equals("ParamTypeTradingOptions") && (!id.startsWith("StockpickerOptions") || id.contains("PickerStoreLogs") || id.contains("PickerEntryType") || id.contains("PickerExitType")) || !isStockpickerStrategy && id.startsWith("StockpickerOptions")) continue;
            JSONObject variable = new JSONObject();
            variable.put("id", (Object)var.getId());
            variable.put("use", true);
            variable.put("type", (Object)var.getType());
            variable.put("name", (Object)name);
            variable.put("paramType", (Object)var.getParamType());
            if (var.getInternalType() == 2) {
                variable.put("start", (Object)"true");
                variable.put("stop", (Object)"false");
                variable.put("step", (Object)"");
            } else {
                Parameter parameter = ParametersSettings.createParameter((Variable)var, (int)30, (int)30, (int)5);
                variable.put("start", parameter.getStart());
                variable.put("stop", parameter.getStop());
                variable.put("step", parameter.getStep());
            }
            variable.put("value", (Object)value);
            variables.put((Object)variable);
        }
        response.put("variables", (Object)variables);
        response.put("symmetryEnabled", xmlS.isSymmetryEnabled());
    }

    private boolean shouldSort(Variables vars) {
        int countGenerated = 0;
        int countDefined = 0;
        for (int a = 0; a < vars.size(); ++a) {
            Variable var = (Variable)vars.get(a);
            if (!var.isAutoGenerated() && !var.isMakeExternal()) continue;
            if (var.isAutoGenerated()) {
                ++countGenerated;
                continue;
            }
            ++countDefined;
        }
        return countDefined <= countGenerated;
    }
}

