/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.applyMassConfig;

import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.List;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ApplyMassConfig
implements Serializable {
    private static final Logger Log = LoggerFactory.getLogger(ApplyMassConfig.class);
    public String loadFromType;
    public String sourceTaskName;
    private Element elSourceTask;
    public boolean applyData;
    public boolean applyDataTradingEngine;
    public boolean applyDataBacktestData;
    public boolean applyDataTestParameters;
    public boolean applyDataDataRangeParts;
    public boolean applyTradingOptions;
    public boolean applyBlocks;
    public boolean applyBlocksSignals;
    public boolean blocksIndicators;
    public boolean blocksapplyBlocksStopLimitEntry;
    public boolean applyBlocksOrderTypes;
    public boolean applyBlocksExitTypes;
    public boolean applyAtm;
    public boolean applyMoneyManagement;
    public boolean applyCrossChecks;
    public boolean whatToBuild;
    public boolean whatToRetest;
    public boolean partsToImprove;
    public boolean geneticOptions;
    public boolean optimization;
    public boolean ranking;
    public List<String> targetTasks = new ArrayList<String>();

    public void init(SQProject sQProject, Element element) throws Exception {
        Object object;
        String string;
        if (element.getChild("LoadFrom") == null) {
            return;
        }
        Element element2 = XMLUtil.getChildElem((Element)element, (String)"LoadFrom");
        this.loadFromType = XMLUtil.getNodeValue((Element)element2, (String)"Type", (String)"file");
        if (this.loadFromType.equals("file")) {
            string = XMLUtil.getNodeValue((Element)element2, (String)"File", null);
            if (string.isBlank()) {
                throw new Exception(L.t((String)"Source file not selected.", (Object[])new Object[0]));
            }
            object = new File(string);
            if (!((File)object).exists()) {
                throw new Exception(L.t((String)"Source file '%s' doesn't exist.", (Object[])new Object[]{((File)object).getAbsolutePath()}));
            }
            if (!((File)object).getName().endsWith("cfx")) {
                throw new Exception("Source file must be '.cfx'.");
            }
            this.elSourceTask = XMLUtil.stringToXmlElement((String)SQFileManager.loadFile(((File)object).getAbsolutePath()));
        } else {
            this.sourceTaskName = XMLUtil.getNodeValue((Element)element2, (String)"Task", null);
            if (!sQProject.containsTask(this.sourceTaskName)) {
                throw new Exception(L.t((String)"Source task '%s' doesn't exist.", (Object[])new Object[]{this.sourceTaskName}));
            }
        }
        string = XMLUtil.getChildElem((Element)element, (String)"WhatToApply");
        this.applyData = XMLUtil.getNodeBooleanValue((Element)string, (String)"Data", (boolean)false);
        this.applyDataTradingEngine = XMLUtil.getNodeBooleanValue((Element)string, (String)"DataTradingEngine", (boolean)false);
        this.applyDataBacktestData = XMLUtil.getNodeBooleanValue((Element)string, (String)"DataBacktestData", (boolean)false);
        this.applyDataTestParameters = XMLUtil.getNodeBooleanValue((Element)string, (String)"DataTestParameters", (boolean)false);
        this.applyDataDataRangeParts = XMLUtil.getNodeBooleanValue((Element)string, (String)"DataDataRangeParts", (boolean)false);
        this.applyTradingOptions = XMLUtil.getNodeBooleanValue((Element)string, (String)"TradingOptions", (boolean)false);
        this.applyBlocks = XMLUtil.getNodeBooleanValue((Element)string, (String)"Blocks", (boolean)false);
        this.applyBlocksSignals = XMLUtil.getNodeBooleanValue((Element)string, (String)"BlocksSignals", (boolean)false);
        this.blocksIndicators = XMLUtil.getNodeBooleanValue((Element)string, (String)"BlocksIndicators", (boolean)false);
        this.blocksapplyBlocksStopLimitEntry = XMLUtil.getNodeBooleanValue((Element)string, (String)"BlocksStopLimitEntry", (boolean)false);
        this.applyBlocksOrderTypes = XMLUtil.getNodeBooleanValue((Element)string, (String)"BlocksOrderTypes", (boolean)false);
        this.applyBlocksExitTypes = XMLUtil.getNodeBooleanValue((Element)string, (String)"BlocksExitTypes", (boolean)false);
        this.applyAtm = XMLUtil.getNodeBooleanValue((Element)string, (String)"Atm", (boolean)false);
        this.applyMoneyManagement = XMLUtil.getNodeBooleanValue((Element)string, (String)"MoneyManagement", (boolean)false);
        this.applyCrossChecks = XMLUtil.getNodeBooleanValue((Element)string, (String)"CrossChecks", (boolean)false);
        this.whatToBuild = XMLUtil.getNodeBooleanValue((Element)string, (String)"WhatToBuild", (boolean)false);
        this.whatToRetest = XMLUtil.getNodeBooleanValue((Element)string, (String)"WhatToRetest", (boolean)false);
        this.partsToImprove = XMLUtil.getNodeBooleanValue((Element)string, (String)"PartsToImprove", (boolean)false);
        this.geneticOptions = XMLUtil.getNodeBooleanValue((Element)string, (String)"GeneticOptions", (boolean)false);
        this.optimization = XMLUtil.getNodeBooleanValue((Element)string, (String)"Optimization", (boolean)false);
        this.ranking = XMLUtil.getNodeBooleanValue((Element)string, (String)"Ranking", (boolean)false);
        object = XMLUtil.getNodeValue((Element)element, (String)"TargetTasks", (String)"");
        this.targetTasks.clear();
        String[] stringArray = ((String)object).split(",");
        for (int i = 0; i < stringArray.length; ++i) {
            String string2 = stringArray[i];
            if (string2.trim().isBlank()) continue;
            this.targetTasks.add(string2);
        }
        if (this.targetTasks.isEmpty()) {
            throw new Exception(L.t((String)"Target task not selected.", (Object[])new Object[0]));
        }
    }

    private void applyChangesToTask(Element element, String string, String string2) throws Exception {
        try {
            Element element2;
            int n;
            List list;
            Object object;
            String string3;
            Object object2;
            Object object3;
            if (this.elSourceTask == null) {
                throw new NullPointerException("Source task is null.");
            }
            Element element3 = this.elSourceTask;
            if (this.applyData && element3.getChild("Data") != null && element.getChild("Data") != null) {
                object3 = (Element)element3.getChild("Data").getChild("Setups").getChildren("Setup").get(0);
                object2 = (Element)element.getChild("Data").getChild("Setups").getChildren("Setup").get(0);
                if (this.applyDataTradingEngine) {
                    object2.setAttribute("engine", XMLUtil.getAttr((Element)object3, (String)"engine"));
                }
                string3 = ((Element)object3.getChildren("Chart").get(0)).getAttributeValue("spread");
                if (this.applyDataBacktestData) {
                    object2.setAttribute("dateFrom", XMLUtil.getAttr((Element)object3, (String)"dateFrom"));
                    object2.setAttribute("dateTo", XMLUtil.getAttr((Element)object3, (String)"dateTo"));
                    object = object2.getChildren("Chart");
                    object.clear();
                    list = object3.getChildren("Chart");
                    for (n = 0; n < list.size(); ++n) {
                        element2 = (Element)list.get(n);
                        object2.addContent((Content)element2.clone());
                    }
                }
                if (this.applyDataTestParameters) {
                    object2.setAttribute("testPrecision", XMLUtil.getAttr((Element)object3, (String)"testPrecision"));
                    object2.setAttribute("slippage", XMLUtil.getAttr((Element)object3, (String)"slippage"));
                    object2.setAttribute("minDist", XMLUtil.getAttr((Element)object3, (String)"minDist"));
                    object2.removeChild("Commissions");
                    object2.addContent((Content)object3.getChild("Commissions").clone());
                    object2.removeChild("Swap");
                    object2.addContent((Content)object3.getChild("Swap").clone());
                    object = object2.getChildren("Chart");
                    for (int i = 0; i < object.size(); ++i) {
                        Element element4 = (Element)object.get(i);
                        element4.setAttribute("spread", string3);
                    }
                }
                if (this.applyDataDataRangeParts && element.getChild("Data").getChild("OutOfSample") != null && element3.getChild("Data").getChild("OutOfSample") != null) {
                    element.getChild("Data").removeChild("OutOfSample");
                    element.getChild("Data").addContent((Content)element3.getChild("Data").getChild("OutOfSample").clone());
                }
            }
            if (this.applyTradingOptions && element3.getChild("Options") != null && element.getChild("Options") != null) {
                element.removeChild("Options");
                element.addContent((Content)element3.getChild("Options").clone());
            }
            if (this.applyBlocks) {
                object3 = element3.getChild("Blocks");
                object2 = element.getChild("Blocks");
                if (object3 != null && object2 != null) {
                    if (object3.getChild("BuildingBlocks") != null && object2.getChild("BuildingBlocks") != null) {
                        if (this.applyBlocksSignals) {
                            object = object2.getChild("BuildingBlocks");
                            list = object.getChildren("Block");
                            for (n = list.size() - 1; n >= 0; --n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("signals")) continue;
                                list.remove(element2);
                            }
                            string3 = object3.getChild("BuildingBlocks");
                            list = string3.getChildren("Block");
                            for (n = 0; n < list.size(); ++n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("signals")) continue;
                                object.addContent((Content)element2.clone());
                            }
                        }
                        if (this.blocksIndicators) {
                            object = object2.getChild("BuildingBlocks");
                            list = object.getChildren("Block");
                            for (n = list.size() - 1; n >= 0; --n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("indicators")) continue;
                                list.remove(element2);
                            }
                            string3 = object3.getChild("BuildingBlocks");
                            list = string3.getChildren("Block");
                            for (n = 0; n < list.size(); ++n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("indicators")) continue;
                                object.addContent((Content)element2.clone());
                            }
                        }
                        if (this.blocksapplyBlocksStopLimitEntry) {
                            object = object2.getChild("BuildingBlocks");
                            list = object.getChildren("Block");
                            for (n = list.size() - 1; n >= 0; --n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("stopLimitBlocks")) continue;
                                list.remove(element2);
                            }
                            string3 = object3.getChild("BuildingBlocks");
                            list = string3.getChildren("Block");
                            for (n = 0; n < list.size(); ++n) {
                                element2 = (Element)list.get(n);
                                if (!XMLUtil.getAttr((Element)element2, (String)"category", (String)"NA").equals("stopLimitBlocks")) continue;
                                object.addContent((Content)element2.clone());
                            }
                        }
                    }
                    if (this.applyBlocksOrderTypes && object3.getChild("OrderTypes") != null && object2.getChild("OrderTypes") != null) {
                        object2.removeChild("OrderTypes");
                        object2.addContent((Content)object3.getChild("OrderTypes").clone());
                    }
                    if (this.applyBlocksExitTypes && object3.getChild("ExitTypes") != null && object2.getChild("ExitTypes") != null) {
                        object2.removeChild("ExitTypes");
                        object2.addContent((Content)object3.getChild("ExitTypes").clone());
                    }
                }
            }
            if (this.applyAtm && (object3 = element3.getChild("ATMs")) != null && ("Build".equals(string) || "Retest".equals(string) || "Optimize".equals(string))) {
                element.removeChild("ATMs");
                element.addContent((Content)element3.getChild("ATMs").clone());
                if (!"Build".equals(string)) {
                    object2 = element.getChild("ATMs");
                    object2.setAttribute("scaleOutType", "1");
                    object2.removeChild("GenerateConfig");
                }
            }
            if (this.applyMoneyManagement && element3.getChild("RiskMoneyManagement") != null && element.getChild("RiskMoneyManagement") != null) {
                element.removeChild("RiskMoneyManagement");
                element.addContent((Content)element3.getChild("RiskMoneyManagement").clone());
            }
            if (this.applyCrossChecks && element3.getChild("CrossChecks") != null && element.getChild("CrossChecks") != null) {
                element.removeChild("CrossChecks");
                element.addContent((Content)element3.getChild("CrossChecks").clone());
            }
            if (this.whatToBuild) {
                if (element3.getChild("WhatToBuild") != null && element.getChild("WhatToBuild") != null) {
                    object3 = XMLUtil.getChildElem((Element)element3.getChild("WhatToBuild"), (String)"BuildMode").clone();
                    object2 = XMLUtil.getChildElem((Element)element.getChild("WhatToBuild"), (String)"BuildMode").clone();
                    element.removeChild("WhatToBuild");
                    element.addContent((Content)element3.getChild("WhatToBuild").clone());
                    if (!this.geneticOptions) {
                        element.getChild("WhatToBuild").removeChild("BuildMode");
                        object2.setAttribute("generationType", object3.getAttributeValue("generationType"));
                        element.getChild("WhatToBuild").addContent((Content)object2);
                    }
                }
                if (element3.getChild("Databanks") != null && element.getChild("Databanks") != null && "Build".equals(string)) {
                    object3 = element.getChild("Databanks").getChildren();
                    object2 = element3.getChild("Databanks").getChildren();
                    for (int i = 0; i < object2.size(); ++i) {
                        if (!((Element)object2.get(i)).getAttributeValue("name").equals("Output")) continue;
                        for (int j = 0; j < object3.size(); ++j) {
                            if (!((Element)object3.get(j)).getAttributeValue("name").equals("Output")) continue;
                            ((Element)element.getChild("Databanks").getChildren().get(j)).setAttribute("value", ((Element)object2.get(i)).getAttributeValue("value"));
                        }
                    }
                }
            }
            if (this.whatToRetest && element3.getChild("Databanks") != null && element.getChild("Databanks") != null && "Retest".equals(string)) {
                element.removeChild("Databanks");
                element.addContent((Content)element3.getChild("Databanks").clone());
            }
            if (this.partsToImprove && element3.getChild("PartsToImprove") != null && element.getChild("PartsToImprove") != null) {
                element.removeChild("PartsToImprove");
                element.addContent((Content)element3.getChild("PartsToImprove").clone());
            }
            if (this.optimization && element3.getChild("Optimization") != null && element.getChild("Optimization") != null) {
                element.removeChild("Optimization");
                element.addContent((Content)element3.getChild("Optimization").clone());
            }
            if (this.ranking && element3.getChild("Rankings") != null && element.getChild("Rankings") != null) {
                element.removeChild("Rankings");
                element.addContent((Content)element3.getChild("Rankings").clone());
            }
        }
        catch (Exception exception) {
            Log.error(String.format("Failed to apply changes to task %s.", string2), (Throwable)exception);
            throw new Exception(L.t((String)"Failed to apply changes to task %s.", (Object[])new Object[]{string2}) + " " + exception.getMessage(), exception);
        }
    }

    public void applyChangesToTasks(SQProject sQProject, ProgressEngine progressEngine) throws Exception {
        if (!this.loadFromType.equals("file")) {
            this.elSourceTask = sQProject.getTaskSettingsByName(this.sourceTaskName);
        }
        if (this.elSourceTask == null) {
            throw new Exception(L.t((String)"Source task is null.", (Object[])new Object[0]));
        }
        for (int i = 0; i < this.targetTasks.size(); ++i) {
            String string = this.targetTasks.get(i);
            if (!sQProject.containsTaskByName(string)) continue;
            ISQTask iSQTask = sQProject.getTaskByName(string);
            Element element = iSQTask.getConfig();
            String string2 = iSQTask.getTitle();
            Log.info(L.t((String)"Applying config to task '%s'", (Object[])new Object[]{string2}));
            if (progressEngine != null) {
                progressEngine.printToLog(L.t((String)"Applying config to task '%s'", (Object[])new Object[]{string2}));
            }
            this.applyChangesToTask(element, iSQTask.getType(), string2);
            iSQTask = sQProject.getTaskByName(string);
            iSQTask.setConfig(element, false, true);
        }
        sQProject.saveConfig();
        if (!MainApp.runInConsoleWithoutActiveWebserver()) {
            this.updateProjecOnFrontend(sQProject, progressEngine == null);
        }
    }

    private void updateProjecOnFrontend(SQProject sQProject, boolean bl) {
        JSONObject jSONObject = new JSONObject().put("projectConfig", (Object)sQProject.toJSON());
        DataToSend dataToSend = new DataToSend("UpdateProject", jSONObject);
        SQWebSocketManager.addToDataQueue(dataToSend, "TASKMANAGER");
    }
}

