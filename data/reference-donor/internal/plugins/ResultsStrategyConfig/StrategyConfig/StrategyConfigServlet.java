/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtest.AutoRetestStrategyConfigModifier
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.strategyConfig.StrategyConfig
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.StrategyConfig;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.AutoRetestStrategyConfigModifier;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.strategyConfig.StrategyConfig;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Arrays;
import java.util.Map;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StrategyConfigServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(StrategyConfigServlet.class);
    private static final String LOCK_STRCONFIGSERVLET = "StrategyConfigServlet";
    private static IResultsGroupProvider rgProvider;
    private StrategyConfig strategyConfig = new StrategyConfig();

    public StrategyConfigServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(args);
            }
            case "loadStrategySettings": {
                return this.onLoadStrategySettings(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onLoadStrategySettings(Map<String, String[]> parameterMap) throws Exception {
        boolean isAlgoWizard = false;
        try {
            isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        ResultsGroup resultsGroup = rgProvider.get(parameterMap, LOCK_STRCONFIGSERVLET);
        JSONObject response = new JSONObject();
        String lastSettingsXml = null;
        try {
            lastSettingsXml = resultsGroup.getLastSettings();
        }
        finally {
            resultsGroup.releaseLock(LOCK_STRCONFIGSERVLET);
        }
        if (lastSettingsXml == null) {
            throw new Exception("Strategy doesn't contain any settings.");
        }
        Element elStrSettings = XMLUtil.stringToElement((String)lastSettingsXml);
        Element task = new Element("Task").addContent((Content)elStrSettings.clone());
        String xml = XMLUtil.elementToString((Element)task);
        Element resourcesXML = ProjectResources.checkTaskResources((Element)elStrSettings);
        if (resourcesXML != null) {
            response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)resourcesXML));
        }
        response.put("xml", (Object)xml);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"projectName", "databankName", "strategyName", "taskType", "taskName"});
        String projectName = parameterMap.get("projectName")[0].toString();
        String taskType = parameterMap.get("taskType")[0].toString();
        String taskName = parameterMap.get("taskName")[0].toString();
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        Element elSettingsCurrent = null;
        String lastSettingsXml = null;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_STRCONFIGSERVLET);
            lastSettingsXml = resultsGroup.getLastSettings();
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = StrategyConfigServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = StrategyConfigServlet.apiErrorJSON((String)L.t((String)"Getting strategy config failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_STRCONFIGSERVLET);
            }
        }
        if (!projectName.equals("AlgoWizard")) {
            SQProject project = ProjectEngine.get((String)projectName);
            Element element = elSettingsCurrent = projectName.equals("AlgoWizard") ? null : project.getTaskSettingsByName(taskName);
            if (taskType.equals("AutomaticRetest")) {
                Element newSettings = XMLUtil.stringToElement((String)lastSettingsXml);
                AutoRetestStrategyConfigModifier.modifySettings((Element)newSettings, (Element)elSettingsCurrent);
                elSettingsCurrent = newSettings;
                taskType = "Retest";
            }
        } else {
            taskType = "Retest";
            try {
                elSettingsCurrent = XMLUtil.stringToElement((String)parameterMap.get("settingsXML")[0].toString());
            }
            catch (Exception e) {
                elSettingsCurrent = null;
            }
        }
        if (lastSettingsXml != null) {
            ISQTask strategyTask = ProjectConfigHelper.createTask((String)taskType, (String)taskName, (String)projectName);
            Element elSettingsStrategy = XMLUtil.stringToElement((String)lastSettingsXml);
            String[] settings = strategyTask.getSettings();
            data = this.strategyConfig.print(Arrays.asList(settings), elSettingsStrategy, elSettingsCurrent);
        }
        response.put("settings", (Object)data);
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

