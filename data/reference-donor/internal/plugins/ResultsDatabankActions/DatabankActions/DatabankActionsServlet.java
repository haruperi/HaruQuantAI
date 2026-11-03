/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.TradingOption
 *  com.strategyquant.tradinglib.Variable
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.databank.DatabankExport
 *  com.strategyquant.tradinglib.options.TradingOptionsList
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.project.websocket.WebSocketNotification
 *  com.strategyquant.tradinglib.propertygrid.IPGParameter
 *  com.strategyquant.tradinglib.strategyConfig.StrategyConfig
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.DatabankActions;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.ValuesMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.TradingOption;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.databank.DatabankExport;
import com.strategyquant.tradinglib.options.TradingOptionsList;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import com.strategyquant.tradinglib.propertygrid.IPGParameter;
import com.strategyquant.tradinglib.strategyConfig.StrategyConfig;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabankActionsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DatabankActionsServlet.class);
    private StrategyConfig strategyConfig = new StrategyConfig();

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getStrategyXml": {
                return this.onGetStrategyXml(args);
            }
            case "saveStrategyXml": {
                return this.onSaveStrategyXml(args);
            }
            case "exportDatabankToCSV": {
                return this.onExportDatabankToCSV(args);
            }
            case "getStrategyParameters": {
                return this.onGetStrategyParameters(args);
            }
            case "setStrategyParameters": {
                return this.onSetStrategyParameters(args);
            }
            case "compareStrategies": {
                return this.onCompareStrategies(args);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onCompareStrategies(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"project", "databank", "strategies"});
        String strategies = this.tryGetParam(args, "strategies")[0];
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        String[] stgs = strategies.split(",");
        Databank databank = this.getDatabank(args);
        ResultsGroup rg1 = null;
        ResultsGroup rg2 = null;
        try {
            rg1 = databank.getLocked(stgs[0], "DACompareStrategies");
            rg2 = databank.getLocked(stgs[1], "DACompareStrategies");
            String rg1Xml = rg1.getLastSettings();
            String rg2Xml = rg2.getLastSettings();
            response.put("strategy1", (Object)rg1.getName());
            response.put("strategy2", (Object)rg2.getName());
            Element el1Xml = XMLUtil.stringToElement((String)rg1Xml);
            Element el2Xml = XMLUtil.stringToElement((String)rg2Xml);
            ArrayList<String> settings = new ArrayList<String>();
            for (Element el : el1Xml.getChildren()) {
                if (settings.contains(el.getName())) continue;
                settings.add(el.getName());
            }
            for (Element el : el2Xml.getChildren()) {
                if (settings.contains(el.getName())) continue;
                settings.add(el.getName());
            }
            data = this.strategyConfig.print(settings, el1Xml, el2Xml);
        }
        finally {
            if (rg1 != null) {
                rg1.releaseLock("DACompareStrategies");
            }
            if (rg2 != null) {
                rg2.releaseLock("DACompareStrategies");
            }
        }
        response.put("settings", (Object)data);
        response.put("success", (Object)L.t((String)"Listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onExportDatabankToCSV(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        this.checkParamExists(args, new String[]{"projectName", "databankName", "path"});
        String projectName = this.tryGetParam(args, "projectName")[0];
        String databankName = this.tryGetParam(args, "databankName")[0];
        boolean useComma = false;
        try {
            useComma = Boolean.parseBoolean(this.tryGetParam(args, "useComma")[0]);
            MainApp.settings().set("CSVExportUseComma", String.valueOf(useComma));
        }
        catch (Exception exception) {
            // empty catch block
        }
        SQProject project = ProjectEngine.get((String)projectName);
        if (!project.getDatabanks().containsKey((Object)databankName)) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{databankName}));
        }
        final Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
        String strategiesSorted = this.getParam(args, "strategies", "all");
        if (strategiesSorted.equals("all")) {
            ArrayList records = databank.getRecordKeys();
            strategiesSorted = String.join((CharSequence)",", records);
        }
        final String view = this.getParam(args, "view", null);
        final String path = args.get("path")[0];
        final boolean _useComma = useComma;
        final String _strategiesSorted = strategiesSorted;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this.exportDatabankContents(databank, path, _strategiesSorted, _useComma, view);
            response.put("success", (Object)L.t((String)"Databank contents exported.", (Object[])new Object[0]));
        } else {
            new Thread(this){
                final /* synthetic */ DatabankActionsServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    try {
                        this.this$0.exportDatabankContents(databank, path, _strategiesSorted, _useComma, view);
                        WebSocketNotification.sendSuccess((String)L.t((String)"Databank content exported", (Object[])new Object[0]), (String[])new String[]{"SQUANT"});
                    }
                    catch (Exception e) {
                        WebSocketNotification.sendError((String)e.getMessage(), (String[])new String[]{"SQUANT"});
                    }
                }
            }.run();
            response.put("success", (Object)L.t((String)"Exporting databank contents.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private void exportDatabankContents(Databank databank, String path, String strategiesSorted, boolean useComma, String customViewName) throws Exception {
        DatabankExport export = new DatabankExport();
        if (path.endsWith("xlsx")) {
            export.toXlsx(databank, path, strategiesSorted, useComma, customViewName);
        } else {
            export.toCsv(databank, path, strategiesSorted, useComma, customViewName, ";");
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSaveStrategyXml(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"project", "databank", "strategy", "xml"});
        String strategyName = args.get("strategy")[0];
        String xml = args.get("xml")[0];
        Databank databank = this.getDatabank(args);
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = databank.getLocked(strategyName, "DASonSaveStrategyXml");
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Strategy '%s' doesn't exist in databank now!", (Object[])new Object[]{strategyName}), e);
        }
        try {
            Element elStrategy = XMLUtil.stringToXmlElement((String)SQUtils.fixRenamedActionParams((String)xml));
            resultsGroup.portfolio().addStrategyXml(elStrategy);
            String filePath = new File(databank.getResultsFilePath(resultsGroup)).getPath();
            databank.getReportSaver().save(resultsGroup, "sqx", filePath, false, 0);
        }
        finally {
            resultsGroup.releaseLock("DASonSaveStrategyXml");
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Strategy saved successfully.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetStrategyXml(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"app", "project", "databank", "strategy"});
        String appName = this.tryGetParam(args, "app")[0];
        String projectName = this.tryGetParam(args, "project")[0];
        String databankName = this.tryGetParam(args, "databank")[0];
        String strategyName = args.get("strategy")[0];
        Databank databank = this.getDatabank(args);
        ResultsGroup resultsGroup = databank.getLocked(strategyName, "DASonGetStrategyXml");
        Element strategyXml = null;
        try {
            strategyXml = resultsGroup.portfolio().getStrategyXml();
        }
        finally {
            resultsGroup.releaseLock("DASonGetStrategyXml");
        }
        if (strategyXml == null) {
            Log.error("Exc.", (Object)"Cannot edit strategy. strategyXml is null.");
            throw new Exception(L.t((String)"Result doesn't contain editable strategy!", (Object[])new Object[0]));
        }
        String xml = XMLUtil.elementToString((Element)strategyXml);
        JSONObject response = new JSONObject();
        response.put("app", (Object)appName);
        response.put("project", (Object)projectName);
        response.put("databank", (Object)databankName);
        response.put("strategy", (Object)strategyName);
        response.put("xml", (Object)xml);
        response.put("lastSettings", (Object)resultsGroup.getLastSettings());
        response.put("success", (Object)L.t((String)"Sources listed.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetStrategyParameters(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"project", "databank", "strategy", "symmetricVariables"});
        String strategyName = args.get("strategy")[0];
        boolean symmetricVariables = Boolean.parseBoolean(args.get("symmetricVariables")[0].toString());
        MainApp.settings().set("editStrategyParamsSymmetry", String.valueOf(symmetricVariables));
        Databank databank = this.getDatabank(args);
        ResultsGroup resultsGroup = databank.getLocked(strategyName, "DASonGetStrategyParameters");
        Element strategyXml = null;
        try {
            strategyXml = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)resultsGroup);
        }
        finally {
            resultsGroup.releaseLock("DASonGetStrategyParameters");
        }
        if (strategyXml == null) {
            Log.error("Exc.", (Object)"Cannot edit strategy. Strategy XML is null.");
            throw new Exception(L.t((String)"Result doesn't contain editable strategy!", (Object[])new Object[0]));
        }
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)strategyXml);
        xmlS.transformToVariables(symmetricVariables, this.buildAllParamTypes());
        Variables variables = xmlS.variables();
        JSONObject response = new JSONObject();
        JSONArray variablesArray = new JSONArray();
        for (int a = 0; a < variables.size(); ++a) {
            Variable variable = (Variable)variables.get(a);
            JSONObject variableObj = new JSONObject();
            variableObj.put("name", (Object)variable.getName());
            variableObj.put("value", (Object)variable.getValue());
            variableObj.put("type", (Object)variable.getType());
            variablesArray.put((Object)variableObj);
        }
        response.put("variables", (Object)variablesArray);
        response.put("success", (Object)L.t((String)"Parameters listed.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSetStrategyParameters(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"project", "databank", "strategy", "symmetricVariables", "parameters"});
        String strategyName = args.get("strategy")[0];
        String parameters = args.get("parameters")[0];
        boolean symmetricVariables = true;
        Databank databank = this.getDatabank(args);
        ResultsGroup resultsGroup = databank.getLocked(strategyName, "DASonSetStrategyParameters");
        Element strategyXml = null;
        try {
            strategyXml = resultsGroup.getStrategyXml();
        }
        finally {
            resultsGroup.releaseLock("DASonSetStrategyParameters");
        }
        if (strategyXml == null) {
            Log.error("Exc.", (Object)"Cannot edit strategy. Strategy XML is null.");
            throw new Exception(L.t((String)"Result doesn't contain editable strategy!", (Object[])new Object[0]));
        }
        String[] params = parameters.split(",");
        HashMap<String, Object> paramMap = new HashMap<String, Object>();
        for (int i = 0; i < params.length; ++i) {
            String[] values = params[i].split("=");
            String name = values[0];
            paramMap.put(name, values[1]);
            if (!name.startsWith("Long") && !name.startsWith("Short") || name.contains("Signal") || name.contains("signal")) continue;
            symmetricVariables = false;
        }
        ArrayList allParamElems = XMLUtil.getNestedElements((Element)strategyXml, (String)"Param");
        for (Element paramElem : allParamElems) {
            String varRef;
            String isVariable = paramElem.getAttributeValue("variable");
            if (isVariable == null || !isVariable.equals("true") || (varRef = paramElem.getTextTrim()) == null || !paramMap.containsKey(varRef)) continue;
            paramElem.setText((String)paramMap.get(varRef));
            paramElem.setAttribute("variable", "false");
        }
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)strategyXml);
        xmlS.transformToVariables(symmetricVariables, this.buildAllParamTypes());
        Variables variables = xmlS.variables();
        for (int a = 0; a < variables.size(); ++a) {
            Variable variable = (Variable)variables.get(a);
            if (!paramMap.containsKey(variable.getName())) continue;
            variable.setFromString((String)paramMap.get(variable.getName()));
        }
        xmlS.transformToNumbers();
        resultsGroup = databank.getLocked(strategyName, "DASonSetStrategyParameters2");
        try {
            try {
                Element lastSettings = XMLUtil.stringToElement((String)resultsGroup.getLastSettings());
                Element elParams = lastSettings.getChild("Options").getChild("BuildTradingOptions").getChild("Params");
                List paramElems = elParams.getChildren("Param");
                List tradingOptions = TradingOptionsList.getInstance().getAvailableClasses();
                for (String paramName : paramMap.keySet()) {
                    boolean processed = false;
                    for (int i = 0; i < tradingOptions.size() && !processed; ++i) {
                        TradingOption option = (TradingOption)tradingOptions.get(i);
                        String optionClass = option.getClass().getSimpleName();
                        ArrayList optionParams = option.getParams();
                        block13: for (int z = 0; z < optionParams.size() && !processed; ++z) {
                            IPGParameter optionParam = (IPGParameter)optionParams.get(z);
                            String paramKey = optionParam.getKey();
                            if (!optionParam.getName().equals(paramName)) continue;
                            for (int s = 0; s < paramElems.size(); ++s) {
                                Element elParam = (Element)paramElems.get(s);
                                String elParamClass = elParam.getAttributeValue("className");
                                String elParamKey = elParam.getAttributeValue("key");
                                if (elParamClass == null || elParamKey == null || !elParamClass.equals(optionClass) || !elParamKey.equals(paramKey)) continue;
                                String value = (String)paramMap.get(paramName);
                                if (optionParam.getType() == 10) {
                                    value = "" + SQTime.HHMMToMinutes((int)Integer.parseInt(value)) * 60;
                                }
                                elParam.setText(value);
                                processed = true;
                                continue block13;
                            }
                        }
                    }
                }
                resultsGroup.setLastSettings(XMLUtil.elementToString((Element)lastSettings));
            }
            catch (Exception e) {
                Log.error("Cannot apply trading options params to last settings", (Throwable)e);
            }
            resultsGroup.portfolio().addStrategyXml(xmlS.getStrategyXml());
            resultsGroup.updated = true;
        }
        finally {
            resultsGroup.releaseLock("DASonSetStrategyParameters2");
        }
        resultsGroup.specialValues().setString("OptimizationParameters", parameters);
        databank.update(resultsGroup.getName(), resultsGroup, true, "DASonSetStrategyParameters3");
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Parameters set.", (Object[])new Object[0]));
        return response.toString();
    }

    private Databank getDatabank(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "project")[0];
        String databankName = this.tryGetParam(args, "databank")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        if (!project.getDatabanks().containsKey((Object)databankName)) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{databankName}));
        }
        return (Databank)project.getDatabanks().get((Object)databankName);
    }

    private ValuesMap buildAllParamTypes() {
        ValuesMap allParamTypes = new ValuesMap();
        allParamTypes.set("ParamTypePeriod", (Object)true);
        allParamTypes.set("ParamTypeShift", (Object)true);
        allParamTypes.set("ParamTypeConstant", (Object)true);
        allParamTypes.set("ParamTypeOtherParam", (Object)true);
        allParamTypes.set("ParamTypeEntryLevel", (Object)true);
        allParamTypes.set("ParamTypeEntryLogic", (Object)true);
        allParamTypes.set("ParamTypeExitUsed", (Object)true);
        allParamTypes.set("ParamTypeExitUnused", (Object)true);
        allParamTypes.set("ParamTypeBoolean", (Object)true);
        allParamTypes.set("ParamTypeTradingOptions", (Object)true);
        return allParamTypes;
    }
}

