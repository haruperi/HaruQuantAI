/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.DataCloner
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionElement
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataCloner;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.generator.StrategyTemplateGenerator;
import com.strategyquant.tradinglib.generator.StrategyTemplateNotFoundException;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectCustomResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.TimeZone;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectResources {
    private static final Logger Log = LoggerFactory.getLogger(ProjectResources.class);
    public static final int StatusDoesntExist = 0;
    public static final int StatusExistsButDiffers = 1;
    public static final int StatusExistsButNotEnoughData = 2;
    public static final int StatusExistsWithDifferentName = 3;
    public static final int ActionTypeLoadProject = 0;
    public static final int ActionTypeLoadTaskConfig = 1;
    public static final int ActionTypeApplyStrategyConfig = 2;
    public static final int ActionTypeLoadTemplate = 3;
    public static final int ActionTypeLoadStrategyToOptimize = 4;
    public static final int ActionTypeResolveProjectResources = 5;
    public static final String ResourcesElementName = "Resources";
    public static final String SymbolsElementName = "Symbols";
    public static final String BrokersElementName = "Brokers";
    public static final String AllBrokersElementName = "AllBrokers";
    public static final String InstrumentsElementName = "Instruments";
    public static final String SessionsElementName = "Sessions";
    public static final String CustomIndicatorsElementName = "CustomIndicators";
    private static final ArrayList<String> symbolsToDownload = new ArrayList();
    private static final ArrayList<CloneInfo> symbolsToClone = new ArrayList();
    private static final DataCloner dataCloner = new DataCloner();
    private static final DataToSend statusData = new DataToSend("ProjectImport", new JSONObject());
    private static final IGridMessageListener listener = new IGridMessageListener(){

        /*
         * WARNING - Removed try catching itself - possible behaviour change.
         */
        public void messageReceived(GridMessage gridMessage) {
            if (gridMessage.getMessageID() == 1) {
                String string = gridMessage.getJobDetails().getJobID();
                String string2 = string.substring("downloadjob_".length());
                long l = lock.writeLock();
                try {
                    symbolsToDownload.remove(string2);
                    if (symbolsToDownload.isEmpty()) {
                        ProjectResources.cloneSymbols();
                    }
                }
                finally {
                    lock.unlock(l);
                }
            }
        }
    };
    private static final StampedLock lock = new StampedLock();

    public static void addResources(SQProject sQProject) throws Exception {
        for (int i = 0; i < sQProject.getTasks().size(); ++i) {
            ISQTask iSQTask = sQProject.getTask(i);
            try {
                ProjectResources.addResources(iSQTask);
                continue;
            }
            catch (Exception exception) {
                Log.error("Adding resources failed", (Throwable)exception);
            }
        }
    }

    public static void addResources(ISQTask iSQTask) throws Exception {
        ProjectResources.addDataResources(iSQTask.getConfig());
        if (iSQTask.getType().equals("Build")) {
            try {
                ProjectResources.addTemplateResources(iSQTask);
            }
            catch (Exception exception) {
                Log.error("Adding template resource failed", (Throwable)exception);
            }
        }
        ProjectCustomResources.addProjectResources(null, iSQTask.getConfig());
    }

    public static void addResources(Element element) throws Exception {
        ProjectResources.addDataResources(element);
        ProjectCustomResources.addProjectResources(null, element);
    }

    private static void addTemplateResources(ISQTask iSQTask) throws Exception {
        String string;
        Element element = iSQTask.getConfig();
        Element element2 = StrategyTemplateGenerator.getConfiguredTemplate(element, string = iSQTask.getCustomName());
        if (element2 != null) {
            Element element3;
            Element element4 = element.getChild(ResourcesElementName);
            if (element4 == null) {
                element4 = new Element(ResourcesElementName);
                element.addContent((Content)element4);
            }
            if ((element3 = element4.getChild("BackupStrategyTemplate")) == null) {
                element3 = new Element("BackupStrategyTemplate");
                element4.addContent((Content)element3);
            } else {
                element3.removeContent();
            }
            element3.addContent((Content)element2.clone());
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void checkBuildTemplates(SQProject sQProject) throws Exception {
        for (int i = 0; i < sQProject.getTasks().size(); ++i) {
            Element element;
            boolean bl = false;
            ISQTask iSQTask = sQProject.getTask(i);
            Element element2 = iSQTask.getConfig();
            try {
                Object object;
                Element element3;
                if (iSQTask.getType() == null || !iSQTask.getType().equals("Build") || (element = element2.getChild("WhatToBuild")) == null || (element3 = element.getChild("StrategyType")) == null || (object = XMLUtil.getStringAttr((Element)element3, (String)"type", null)) == null || !((String)object).equals("template")) continue;
                bl = true;
                try {
                    StrategyTemplateGenerator.getConfiguredTemplate(element2, iSQTask.getCustomName());
                }
                catch (StrategyTemplateNotFoundException strategyTemplateNotFoundException) {
                    String string = strategyTemplateNotFoundException.getTemplateFile();
                    String string2 = strategyTemplateNotFoundException.getTaskName();
                    ProjectResources.resolveBuildTemplate(sQProject, string2, string, element2);
                }
                continue;
            }
            catch (Exception exception) {
                Log.error("Checking template build task failed", (Throwable)exception);
                continue;
            }
            finally {
                if (!bl && (element = element2.getChild(ResourcesElementName)) != null) {
                    element.removeChild("BackupStrategyTemplate");
                }
            }
        }
    }

    private static void resolveBuildTemplate(SQProject sQProject, String string, String string2, Element element) throws Exception {
        Object object;
        String string3;
        if (string2 == null) {
            throw new Exception(L.t((String)"Template file of build task '%s' not specified", (Object[])new Object[]{string}));
        }
        Element element2 = element.getChild(ResourcesElementName);
        if (element2 == null) {
            throw new Exception(L.t((String)"Template file '%s' of build task '%s' not found", (Object[])new Object[]{string2, string}));
        }
        Element element3 = element2.getChild("BackupStrategyTemplate");
        if (element3 == null) {
            throw new Exception(L.t((String)"Template file '%s' of build task '%s' not found", (Object[])new Object[]{string2, string}));
        }
        String string4 = "Build task '" + string + "' uses template<br>'" + string2 + "',<br> but the template doesn't exist in this location.<br><br>Do you want to create it from backup? (Template will be stored in user/settings/StrategyTemplates)";
        sQProject.userConfirm.awaitConfirmation("Strategy template not found", string4);
        if (sQProject.userConfirm.isConfirmed()) {
            Element element4 = XMLUtil.getChildElem((Element)element3, (String)"StrategyFile");
            string3 = SQUtils.stripExtension((String)new File(string2).getName()) + ".sqw";
            File file = new File(SQPaths.strategyTemplatesDirPath + "/" + string3);
            DataToSend dataToSend = new DataToSend();
            dataToSend.setName("TemplatePathChange");
            Element element5 = ProjectConfigHelper.getTaskConfigByName(sQProject.getConfig(), string);
            String string5 = element5.getAttributeValue("taskXMLFile");
            dataToSend.setDataObject(new JSONObject().put("taskName", (Object)string).put("taskXMLFile", (Object)string5).put("templateFile", (Object)string3));
            SQWebSocketManager.addToDataQueue(dataToSend, SQWebSocketManager.getProductCode(sQProject.getName()));
            if (file.exists()) {
                object = file.getAbsolutePath().replace("\\", "/").replace(MainApp.getDataPath(), "");
                sQProject.userConfirm.awaitConfirmation("Strategy build template already exists", "Strategy template<br>'" + (String)object + "'<br>already exists in this location.<br><br>Do you want to overwrite it?");
                if (sQProject.userConfirm.isConfirmed()) {
                    XMLUtil.xmlToFile((Element)element4, (File)file);
                }
            } else {
                XMLUtil.xmlToFile((Element)element4, (File)file);
            }
        } else {
            throw new TaskStoppedException();
        }
        object = XMLUtil.getChildElem((Element)element, (String)"WhatToBuild");
        Element element6 = XMLUtil.getChildElem((Element)object, (String)"StrategyType");
        element6.setAttribute("templateFile", string3);
        sQProject.saveConfig();
    }

    public static void addDataResources(Element element) {
        Object object;
        Object object2;
        int n;
        element.removeChildren(ResourcesElementName);
        ArrayList arrayList = XMLUtil.getNestedElements((Element)element, (String)"Setup");
        Element element2 = new Element(ResourcesElementName);
        Element element3 = new Element(SymbolsElementName);
        Element element4 = new Element(SessionsElementName);
        Element element5 = new Element(BrokersElementName);
        Element element6 = new Element(InstrumentsElementName);
        ArrayList<String> arrayList2 = new ArrayList<String>();
        ArrayList<String> arrayList3 = new ArrayList<String>();
        HashMap<String, Long> hashMap = new HashMap<String, Long>();
        HashMap<String, Long> hashMap2 = new HashMap<String, Long>();
        HashSet<Integer> hashSet = new HashSet<Integer>();
        HashSet<InstrumentInfo> hashSet2 = new HashSet<InstrumentInfo>();
        String string = null;
        for (n = 0; n < arrayList.size(); ++n) {
            object2 = (Element)arrayList.get(n);
            if (!object2.getParentElement().getParentElement().getName().equals("Data")) continue;
            string = object2.getAttributeValue("engine");
            break;
        }
        for (n = 0; n < arrayList.size(); ++n) {
            object2 = (Element)arrayList.get(n);
            if (object2.getParentElement().getParentElement().getName().equals("CustomData") || ("Stockpicker".equals(string) || "Single-asset cloud strategy".equals(string)) && object2.getParentElement().getParentElement().getParentElement().getName().equals("RetestOnAdditionalMarkets")) continue;
            String string2 = object2.getAttributeValue("session");
            if (ProjectResources.checkIfSaveSession(string2, arrayList2)) {
                try {
                    element4.addContent((Content)ProjectResources.createSessionElement(string2));
                    arrayList2.add(string2);
                }
                catch (Exception exception) {
                    Log.error("Error while adding session to resources - " + exception.getMessage());
                }
            }
            object = object2.getChildren("Chart");
            long l = 0L;
            try {
                l = SQTime.parseDateToMilis((String)object2.getAttributeValue("dateFrom"));
            }
            catch (Exception exception) {
                // empty catch block
            }
            long l2 = 0L;
            try {
                l2 = SQTime.parseDateToMilis((String)object2.getAttributeValue("dateTo"));
            }
            catch (Exception exception) {
                // empty catch block
            }
            for (int i = 0; i < object.size(); ++i) {
                DataInfo dataInfo;
                Element element7 = (Element)object.get(i);
                String string3 = element7.getAttributeValue("symbol");
                l = ProjectResources.checkDate(hashMap, string3, l, true);
                l2 = ProjectResources.checkDate(hashMap2, string3, l2, false);
                if (string3 == null || string3.equals("Same as main chart")) continue;
                DataInfo dataInfo2 = DataManager.getDataInfo((String)"History", (String)string3);
                if (dataInfo2 == null) {
                    Log.error(String.format("Error while adding symbol to resources - Symbol '%s' doesn't exist", string3));
                    continue;
                }
                String string4 = null;
                String string5 = null;
                String string6 = null;
                String string7 = null;
                if (dataInfo2.sourceDataId > 0) {
                    dataInfo = DataManager.getDataInfo((String)"History", (int)dataInfo2.sourceDataId);
                    if (dataInfo == null) {
                        Log.error(String.format("Error while adding symbol to resources - Source symbol with id '%d' doesn't exist", dataInfo2.sourceDataId));
                        continue;
                    }
                    string4 = dataInfo.symbol;
                    string5 = dataInfo.timezone;
                    string6 = dataInfo.uSymbol;
                    string7 = dataInfo.uSymbolName;
                }
                if (arrayList3.contains(string3)) continue;
                try {
                    dataInfo = ProjectResources.createSymbolElement(dataInfo2, l, l2);
                    if (string4 != null) {
                        dataInfo.setAttribute("cloneFrom", string4);
                        dataInfo.setAttribute("sourceTimezone", string5);
                        if (string6 != null) {
                            dataInfo.setAttribute("uSymbol", string6);
                        }
                        if (string7 != null) {
                            dataInfo.setAttribute("uSymbolName", string7);
                        }
                    }
                    if (dataInfo2.symbolInfo.broker != -1) {
                        hashSet2.add(dataInfo2.symbolInfo);
                        hashSet.add(dataInfo2.symbolInfo.broker);
                    }
                    if (dataInfo2.brokerId != -1) {
                        hashSet.add(dataInfo2.brokerId);
                    }
                    element3.addContent((Content)dataInfo);
                    arrayList3.add(string3);
                    continue;
                }
                catch (Exception exception) {
                    Log.error("Error while adding symbol to resources", (Throwable)exception);
                }
            }
        }
        String string8 = ProjectResources.getMarketOpenSession(element);
        if (ProjectResources.checkIfSaveSession(string8, arrayList2)) {
            try {
                element4.addContent((Content)ProjectResources.createSessionElement(string8));
                arrayList2.add(string8);
            }
            catch (Exception exception) {
                Log.error("Error while adding session (MarketOpenSession) to resources - " + exception.getMessage());
            }
        }
        object2 = hashSet.iterator();
        while (object2.hasNext()) {
            int n2 = (Integer)object2.next();
            object = BrokerManager.getInstance().getBroker(Integer.valueOf(n2));
            if (object == null) {
                Log.warn("Broker not found for id: {}", (Object)n2);
                continue;
            }
            element5.addContent((Content)ProjectResources.createBrokerElement((BrokerDto)object));
        }
        for (InstrumentInfo instrumentInfo : hashSet2) {
            element6.addContent((Content)instrumentInfo.getXML());
        }
        element2.addContent((Content)element3);
        element2.addContent((Content)element5);
        element2.addContent((Content)element6);
        element2.addContent((Content)element4);
        element.addContent((Content)element2);
    }

    private static boolean checkIfSaveSession(String string, List<String> list) {
        return string != null && !string.equals("No Session") && !string.equals("Forex_245") && !string.equals("Forex_247") && !list.contains(string) && !string.equals("null");
    }

    public static String getSession(Element element) {
        Element element2 = element.getChild("Options");
        if (element2 == null) {
            return null;
        }
        Element element3 = element2.getChild("BuildTradingOptions");
        if (element3 == null) {
            return null;
        }
        Element element4 = element3.getChild("Params");
        if (element4 == null) {
            return null;
        }
        List list = element4.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element5 = (Element)list.get(i);
            String string = element5.getAttributeValue("key");
            if (!string.equals("Session")) continue;
            return element5.getValue();
        }
        return null;
    }

    public static String getMarketOpenSession(Element element) {
        Element element2 = element.getChild("Options");
        if (element2 == null) {
            return null;
        }
        Element element3 = element2.getChild("BuildTradingOptions");
        if (element3 == null) {
            return null;
        }
        Element element4 = element3.getChild("Params");
        if (element4 == null) {
            return null;
        }
        List list = element4.getChildren("Param");
        for (int i = 0; i < list.size(); ++i) {
            Element element5 = (Element)list.get(i);
            String string = element5.getAttributeValue("key");
            if (!string.equals("MarketOpenSession")) continue;
            return element5.getValue();
        }
        return null;
    }

    public static Element createBrokerElement(BrokerDto brokerDto) {
        Element element = new Element("Broker");
        element.setAttribute("id", String.valueOf(brokerDto.getId()));
        element.setAttribute("name", brokerDto.getName());
        element.setAttribute("description", brokerDto.getDesc());
        element.setAttribute("timezone", brokerDto.getMtTimezone());
        element.setAttribute("postfix", brokerDto.getPostfix());
        element.setAttribute("mtUse", String.valueOf(brokerDto.isMtUse()));
        element.setAttribute("spUse", String.valueOf(brokerDto.isStockPickerUse()));
        return element;
    }

    private static long checkDate(HashMap<String, Long> hashMap, String string, long l, boolean bl) {
        if (l != 0L && hashMap.containsKey(string)) {
            long l2 = hashMap.get(string);
            if (bl && l < l2 || !bl && l > l2) {
                hashMap.put(string, l);
            } else {
                return l2;
            }
        }
        return l;
    }

    public static Element checkProjectResources(File file, Element element) throws Exception {
        Element element2;
        String string2;
        if (SQProject.projectIsOlderThan136(element)) {
            return ProjectResources.checkTaskResources(element);
        }
        ArrayList<Element> arrayList = new ArrayList<Element>();
        HashMap<String, Element> hashMap = SQFileManager.loadTaskConfigs(file);
        for (String string2 : hashMap.keySet()) {
            element2 = hashMap.get(string2);
            arrayList.add(element2);
        }
        Element element3 = null;
        string2 = null;
        element2 = null;
        ArrayList<String> arrayList2 = new ArrayList<String>();
        ArrayList<String> arrayList3 = new ArrayList<String>();
        for (int i = 0; i < arrayList.size(); ++i) {
            String string3;
            Object object;
            Element element4;
            Element element5 = (Element)arrayList.get(i);
            Element element6 = ProjectResources.checkTaskResources(element5);
            if (element6 == null) continue;
            if (element3 == null) {
                element3 = new Element(ResourcesElementName);
            }
            if ((element4 = element6.getChild(SymbolsElementName)) != null) {
                if (string2 == null) {
                    string2 = new Element(SymbolsElementName);
                    element3.addContent((Content)string2);
                }
                object = element4.getChildren("Symbol");
                for (int j = object.size() - 1; j >= 0; --j) {
                    Element element7 = (Element)object.get(j);
                    string3 = element7.getAttributeValue("name");
                    if (arrayList2.contains(string3)) continue;
                    string2.addContent((Content)element7.clone());
                    arrayList2.add(string3);
                }
            }
            if ((object = element6.getChild(SessionsElementName)) == null) continue;
            if (element2 == null) {
                element2 = new Element(SessionsElementName);
                element3.addContent((Content)element2);
            }
            List list = object.getChildren("Session");
            for (int j = list.size() - 1; j >= 0; --j) {
                string3 = (Element)list.get(j);
                String string4 = string3.getAttributeValue("name");
                if (arrayList3.contains(string4)) continue;
                element2.addContent((Content)string3.clone());
                arrayList3.add(string4);
            }
        }
        return element3;
    }

    public static Element checkTaskResources(Element element) throws Exception {
        return ProjectResources.checkTaskResources(element, false);
    }

    /*
     * Unable to fully structure code
     * Could not resolve type clashes
     */
    public static Element checkTaskResources(Element var0, boolean var1_1) throws Exception {
        if (var0.getName().equals("Task") && var0.getChild("Settings") != null) {
            var0 = var0.getChild("Settings");
        }
        var2_2 = true;
        var3_3 = false;
        try {
            var4_4 = XMLUtil.getNestedElements((Element)var0, (String)"Chart");
            for (var5_6 = 0; var5_6 < var4_4.size(); ++var5_6) {
                var6_9 = (Element)var4_4.get(var5_6);
                var7_10 = var6_9.getAttributeValue("timeframe");
                if (var7_10 == null || TimeframeManager.TFExists((String)var7_10)) continue;
                TimeframeManager.addTimeframe((String)var7_10);
                var3_3 = true;
            }
        }
        catch (Exception var4_5) {
            ProjectResources.Log.error("Error while checking missing timeframes", (Throwable)var4_5);
        }
        if (var3_3) {
            SQWebSocketManager.addToDataQueue(WSDataObjects.getTimeframes(), new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        if ((var4_4 = var0.getChild("Resources")) == null || var4_4.getChildren().isEmpty() || var4_4.getChild("Symbols") == null || var4_4.getChild("Symbols").getChildren().isEmpty()) {
            var5_7 = null;
            var6_9 = null;
            var11_13 = null;
            var12_15 = null;
            var4_4 = new Element("Resources");
            var13_17 = new Element("Symbols");
            var4_4.addContent((Content)var13_17);
            try {
                var14_22 = var0.getChild("Data");
                if (var14_22 == null) ** GOTO lbl267
                var15_28 = var14_22.getChild("Setups");
                var16_31 = var15_28.getChildren("Setup");
                for (var17_35 = 0; var17_35 < var16_31.size(); ++var17_35) {
                    var18_39 = (Element)var16_31.get(var17_35);
                    var7_11 = XMLUtil.parseDate((String)var18_39.getAttributeValue("dateFrom"));
                    var9_37 = XMLUtil.parseDate((String)var18_39.getAttributeValue("dateTo"));
                    var19_43 = var18_39.getChildren("Chart");
                    for (var20_45 = 0; var20_45 < var19_43.size(); ++var20_45) {
                        if (var20_45 == 0) {
                            var11_13 = var5_7 = ((Element)var19_43.get(var20_45)).getAttributeValue("symbol");
                            var6_9 = ((Element)var19_43.get(var20_45)).getAttributeValue("timeframe");
                            var12_15 = var6_9;
                        } else {
                            var5_7 = ((Element)var19_43.get(var20_45)).getAttributeValue("symbol");
                            var6_9 = ((Element)var19_43.get(var20_45)).getAttributeValue("timeframe");
                            if (var5_7.equals("Same as main chart")) {
                                var5_7 = var11_13;
                            }
                            if (var6_9.equals("Same as main data")) {
                                var6_9 = var12_15;
                            }
                        }
                        var21_47 = null;
                        var22_49 = DataManager.getDataInfo((String)"History", (String)var5_7);
                        if (var22_49 == null) {
                            var21_47 = new Element("Symbol");
                            var21_47.setAttribute("name", var5_7);
                            var21_47.setAttribute("precision", (String)var6_9);
                            var21_47.setAttribute("status", String.valueOf(0));
                        } else {
                            var23_51 = SQTime.correctDayStart((long)var22_49.dateFrom);
                            var25_52 = SQTime.correctDayEnd((long)var22_49.dateTo);
                            var27_56 = TimeframeManager.getMillis((String)var6_9);
                            var29_61 = TimeframeManager.getMillis((String)var22_49.timeframe);
                            if (var29_61 > var27_56) {
                                var21_47 = new Element("Symbol");
                                var21_47.setAttribute("name", var5_7);
                                var21_47.setAttribute("precision", (String)var6_9);
                                var21_47.setAttribute("status", String.valueOf(1));
                            } else if (var23_51 > var7_11 || var25_52 < var9_37) {
                                var21_47 = new Element("Symbol");
                                var21_47.setAttribute("name", var5_7);
                                var21_47.setAttribute("status", String.valueOf(2));
                                var21_47.setAttribute("missingDays", "" + ProjectResources.getMissingDays(var23_51, var25_52, var7_11, var9_37));
                            }
                        }
                        if (var21_47 == null) continue;
                        var23_51 = 0L;
                        if (var6_9 != null && !var6_9.isEmpty()) {
                            var23_51 = TimeframeManager.getMillis((String)var6_9);
                        }
                        var25_53 = null;
                        var26_54 = var13_17.getChildren("Symbol");
                        for (Element var28_59 : var26_54) {
                            if (!var5_7.equals(var28_59.getAttributeValue("name"))) continue;
                            var25_53 = var28_59;
                            break;
                        }
                        if (var25_53 == null) {
                            var13_17.addContent((Content)var21_47);
                            var2_2 = false;
                            continue;
                        }
                        var27_57 = var25_53.getAttributeValue("precision");
                        if (var27_57 == null || var27_57.isEmpty()) {
                            var27_57 = var6_9;
                        }
                        var28_60 = 0L;
                        if (var27_57 != null && !var27_57.isEmpty()) {
                            var28_60 = TimeframeManager.getMillis((String)var27_57);
                        }
                        if (var23_51 <= 0L || var28_60 != 0L && var23_51 >= var28_60) continue;
                        var30_63 = var21_47.getAttributeValue("precision");
                        if (var30_63 != null) {
                            var25_53.setAttribute("precision", var30_63);
                        }
                        var2_2 = false;
                    }
                }
            }
            catch (Exception var14_23) {
                ProjectResources.Log.error("Cannot check resources from XML config", (Throwable)var14_23);
            }
        } else {
            var5_8 = new ArrayList<E>();
            var6_9 = new ArrayList<E>();
            if (var1_1) {
                var5_8 = ProjectResources.extractAWSymbols(var0);
                var6_9 = ProjectResources.findInstrumentsBySymbols((Element)var4_4, var5_8);
            }
            try {
                var7_10 = var4_4.getChild("Symbols");
                var8_64 = var4_4.getChild("Sessions");
                var9_38 = var4_4.getChild("Instruments");
                var10_65 = var4_4.getChild("Brokers");
                var11_14 = var4_4.getChild("CustomIndicators");
                if (var7_10 != null) {
                    var12_16 = var7_10.getChildren("Symbol");
                    for (var13_18 = var12_16.size() - 1; var13_18 >= 0; --var13_18) {
                        var14_24 = "NA";
                        try {
                            var15_29 /* !! */  = (Element)var12_16.get(var13_18);
                            var16_32 /* !! */  = var15_29 /* !! */ .getChild("InstrumentInfo");
                            var17_36 /* !! */  = null;
                            if (var16_32 /* !! */  != null) {
                                var17_36 /* !! */  = new InstrumentInfo(var16_32 /* !! */ );
                            }
                            var14_24 = XMLUtil.getAttr((Element)var15_29 /* !! */ , (String)"name");
                            var18_40 = XMLUtil.getIntAttr((Element)var15_29 /* !! */ , (String)"source");
                            var19_44 = XMLUtil.getIntAttr((Element)var15_29 /* !! */ , (String)"barType");
                            var20_46 = XMLUtil.getAttr((Element)var15_29 /* !! */ , (String)"precision");
                            var21_48 = XMLUtil.getAttr((Element)var15_29 /* !! */ , (String)"timezone");
                            var22_50 = XMLUtil.getLongAttr((Element)var15_29 /* !! */ , (String)"dateFrom");
                            var24_66 = XMLUtil.getLongAttr((Element)var15_29 /* !! */ , (String)"dateTo");
                            var26_55 = DataManager.getDataInfo((String)"History", (String)var14_24);
                            if (var26_55 == null) {
                                var15_29 /* !! */ .setAttribute("status", String.valueOf(0));
                                var2_2 = false;
                            } else {
                                var27_58 = SQTime.correctDayStart((long)var26_55.dateFrom);
                                var29_62 = SQTime.correctDayEnd((long)var26_55.dateTo);
                                if (!(var26_55.source == var18_40 && var26_55.barTimeType == var19_44 && var26_55.timeframe != null && var26_55.timeframe.equals(var20_46) && ProjectResources.checkTimeZone(var26_55.timezone, var21_48) && ProjectResources.compareInstruments(var26_55.symbolInfo, var17_36 /* !! */ ))) {
                                    var15_29 /* !! */ .setAttribute("status", String.valueOf(1));
                                    var2_2 = false;
                                } else if (var27_58 > var22_50 || var29_62 < var24_66) {
                                    var15_29 /* !! */ .setAttribute("status", String.valueOf(2));
                                    var15_29 /* !! */ .setAttribute("missingDays", "" + ProjectResources.getMissingDays(var27_58, var29_62, var22_50, var24_66));
                                    var2_2 = false;
                                } else {
                                    var7_10.removeContent((Content)var15_29 /* !! */ );
                                }
                            }
                            if (!var1_1 || var5_8.contains(var14_24)) continue;
                            var7_10.removeContent((Content)var15_29 /* !! */ );
                            continue;
                        }
                        catch (Exception var15_30) {
                            ProjectResources.Log.error(String.format("Cannot check symbol '%s'", new Object[]{var14_24}), (Throwable)var15_30);
                        }
                    }
                }
                if (var8_64 != null) {
                    var12_16 = var8_64.getChildren("Session");
                    for (var13_18 = var12_16.size() - 1; var13_18 >= 0; --var13_18) {
                        var14_24 = (Element)var12_16.get(var13_18);
                        var15_29 /* !! */  = var14_24.getAttributeValue("name");
                        try {
                            var16_32 /* !! */  = SessionManager.getSession((String)var15_29 /* !! */ );
                            if (var16_32 /* !! */  == null) {
                                var14_24.setAttribute("status", String.valueOf(0));
                                var2_2 = false;
                                continue;
                            }
                            if (!XMLUtil.elementToString((Element)ProjectResources.createSessionElement((String)var15_29 /* !! */ )).equals(XMLUtil.elementToString((Element)var14_24))) {
                                var14_24.setAttribute("status", String.valueOf(1));
                                var2_2 = false;
                                continue;
                            }
                            var8_64.removeContent((Content)var14_24);
                            continue;
                        }
                        catch (Exception var16_33) {
                            ProjectResources.Log.error("Cannot check session", (Throwable)var16_33);
                        }
                    }
                }
                if (var10_65 != null) {
                    var12_16 = var10_65.getChildren("Broker");
                    var13_19 = new Element("AllBrokers");
                    for (var14_25 = var12_16.size() - 1; var14_25 >= 0; --var14_25) {
                        var15_29 /* !! */  = (Element)var12_16.get(var14_25);
                        var16_32 /* !! */  = var15_29 /* !! */ .getAttributeValue("name");
                        var17_36 /* !! */  = var15_29 /* !! */ .getAttributeValue("timezone");
                        var13_19.addContent((Content)var15_29 /* !! */ .clone());
                        try {
                            var18_41 = BrokerManager.getInstance().getBroker((String)var16_32 /* !! */ );
                            if (var18_41 == null) {
                                var15_29 /* !! */ .setAttribute("status", String.valueOf(0));
                                var2_2 = false;
                                continue;
                            }
                            if (!var18_41.getMtTimezone().equals(var17_36 /* !! */ )) {
                                var15_29 /* !! */ .setAttribute("status", String.valueOf(1));
                                var2_2 = false;
                                continue;
                            }
                            var10_65.removeContent((Content)var15_29 /* !! */ );
                            continue;
                        }
                        catch (Exception var18_42) {
                            ProjectResources.Log.error("Cannot check broker", (Throwable)var18_42);
                        }
                    }
                    var4_4.addContent((Content)var13_19);
                }
                if (var9_38 != null) {
                    var12_16 = var9_38.getChildren("InstrumentInfo");
                    for (var13_20 = var12_16.size() - 1; var13_20 >= 0; --var13_20) {
                        var14_26 = (Element)var12_16.get(var13_20);
                        var15_29 /* !! */  = var14_26.getAttributeValue("instrument");
                        try {
                            if (!InstrumentManager.checkInstrumentExists((String)var15_29 /* !! */ )) {
                                var14_26.setAttribute("status", String.valueOf(0));
                                var2_2 = false;
                            } else {
                                var16_32 /* !! */  = InstrumentManager.getInstrumentInfo((String)var15_29 /* !! */ );
                                if (!XMLUtil.elementToString((Element)var16_32 /* !! */ .getXML()).equals(XMLUtil.elementToString((Element)var14_26))) {
                                    var14_26.setAttribute("status", String.valueOf(1));
                                    var2_2 = false;
                                } else {
                                    var9_38.removeContent((Content)var14_26);
                                }
                            }
                            if (!var1_1 || var6_9.contains(var15_29 /* !! */ )) continue;
                            var9_38.removeContent((Content)var14_26);
                            continue;
                        }
                        catch (Exception var16_34) {
                            ProjectResources.Log.error("Cannot check instrument", (Throwable)var16_34);
                        }
                    }
                }
                if (var1_1 && var11_14 != null) {
                    var12_16 = var11_14.getChildren("CustomIndicator");
                    for (var13_21 = var12_16.size() - 1; var13_21 >= 0; --var13_21) {
                        var14_27 = (Element)var12_16.get(var13_21);
                        var15_29 /* !! */  = var14_27.getText();
                        if (CustomDataManager.checkDataExists((String)var15_29 /* !! */ )) {
                            var11_14.removeContent((Content)var14_27);
                            continue;
                        }
                        var14_27.setAttribute("status", "0");
                        var2_2 = false;
                    }
                }
            }
            catch (Exception var7_12) {
                ProjectResources.Log.error("Cannot check resources from XML config", (Throwable)var7_12);
                throw new Exception("Cannot check XML config resources - " + var7_12.getMessage());
            }
        }
lbl267:
        // 4 sources

        if (var2_2) {
            return null;
        }
        return var4_4;
    }

    private static List<String> extractAWSymbols(Element element) {
        ArrayList<String> arrayList = new ArrayList<String>();
        Element element2 = element.getChild("Data");
        if (element2 != null) {
            Element element3 = element2.getChild("Setups");
            List list = element3.getChildren("Setup");
            for (int i = 0; i < list.size(); ++i) {
                Element element4 = (Element)list.get(i);
                List list2 = element4.getChildren("Chart");
                for (int j = 0; j < list2.size(); ++j) {
                    String string = ((Element)list2.get(j)).getAttributeValue("symbol");
                    arrayList.add(string);
                }
            }
        }
        return arrayList;
    }

    private static List<String> findInstrumentsBySymbols(Element element, List<String> list) {
        ArrayList<String> arrayList = new ArrayList<String>();
        if (element == null) {
            return arrayList;
        }
        Element element2 = element.getChild(SymbolsElementName);
        if (element2 == null) {
            return arrayList;
        }
        List list2 = element2.getChildren("Symbol");
        block0: for (String string : list) {
            for (Element element3 : list2) {
                String string2;
                if (!string.equals(element3.getAttributeValue("name"))) continue;
                Element element4 = element3.getChild("InstrumentInfo");
                if (element4 == null || (string2 = element4.getAttributeValue("instrument")) == null || string2.isEmpty()) continue block0;
                arrayList.add(string2);
                continue block0;
            }
        }
        return arrayList;
    }

    private static boolean checkTimeZone(String string, String string2) {
        boolean bl;
        if (string == null || string2 == null) {
            return true;
        }
        boolean bl2 = string.equals("Etc/UCT") || string.startsWith("(UTC)");
        boolean bl3 = bl = string2.equals("Etc/UCT") || string2.startsWith("(UTC)");
        if (bl2 && bl || string.equals(string2)) {
            return true;
        }
        int n = bl2 ? 0 : TimeZone.getTimeZone(string).getRawOffset();
        int n2 = bl ? 0 : TimeZone.getTimeZone(string2).getRawOffset();
        return n == n2;
    }

    private static int getMissingDays(long l, long l2, long l3, long l4) {
        long l5 = 0L;
        if (l == 0L || l2 == 0L) {
            l5 = l4 - l3;
        } else {
            if (l > l3) {
                l5 += l - l3;
            }
            if (l2 < l4) {
                l5 += l4 - l2;
            }
        }
        return (int)(l5 / 86400000L);
    }

    public static boolean resolveResources(Element element, Element element2, HashMap<String, Element> hashMap, JSONArray jSONArray, Element element3) throws Exception {
        try {
            String string;
            Object object;
            Object object2;
            String string2;
            int n;
            Integer n2;
            String string3;
            String string4;
            Object object3;
            String string52;
            Element element4 = element.getChild(SymbolsElementName);
            Element element5 = element.getChild(SessionsElementName);
            Element element6 = element.getChild(InstrumentsElementName);
            Element element7 = element.getChild(BrokersElementName);
            Element element8 = element.getChild(AllBrokersElementName);
            ArrayList arrayList = new ArrayList();
            if (element4 != null) {
                arrayList.addAll(element4.getChildren("Symbol"));
            }
            ArrayList<Element> arrayList2 = new ArrayList<Element>();
            arrayList2.add(element2);
            if (hashMap != null) {
                for (String string52 : hashMap.keySet()) {
                    arrayList2.add(hashMap.get(string52));
                }
            }
            Object object4 = "";
            string52 = "";
            String string6 = "";
            String string7 = "";
            ArrayList arrayList3 = new ArrayList();
            if (element8 != null) {
                arrayList3.addAll(element8.getChildren("Broker"));
            }
            HashMap<Integer, Object> hashMap2 = new HashMap<Integer, Object>();
            for (int i = arrayList3.size() - 1; i >= 0; --i) {
                Element element9 = (Element)arrayList3.get(i);
                BrokerDto brokerDto = ProjectResources.loadBrokerElement(element9);
                hashMap2.put(brokerDto.getId(), brokerDto);
            }
            ArrayList arrayList4 = new ArrayList();
            if (element7 != null) {
                arrayList4.addAll(element7.getChildren("Broker"));
            }
            boolean bl = false;
            for (int i = arrayList4.size() - 1; i >= 0; --i) {
                Element element10 = (Element)arrayList4.get(i);
                object3 = XMLUtil.getAttr((Element)element10, (String)"action", (String)"ignore");
                BrokerDto brokerDto = ProjectResources.loadBrokerElement(element10);
                if (((String)object3).equals("ignore")) continue;
                string4 = element10.getAttributeValue("name");
                if (((String)object3).equals("add")) {
                    string3 = ProjectResources.generateNewBrokerName(string4);
                    n2 = brokerDto.getId();
                    brokerDto.setId(null);
                    brokerDto.setName(string3);
                    BrokerManager.getInstance().saveBroker(brokerDto);
                    hashMap2.put(n2, brokerDto);
                    bl = true;
                    continue;
                }
                if (((String)object3).equals("replace")) {
                    string3 = element10.getAttributeValue("replaceBroker");
                    n2 = BrokerManager.getInstance().getBroker(string3);
                    if (brokerDto == null) {
                        throw new Exception(L.t((String)"Replace broker '%s' doesn't exist", (Object[])new Object[]{string3}));
                    }
                    hashMap2.put(brokerDto.getId(), n2);
                    continue;
                }
                throw new Exception(L.t((String)"Unknown broker action '%s'", (Object[])new Object[]{object3}));
            }
            ArrayList arrayList5 = new ArrayList();
            if (element6 != null) {
                arrayList5.addAll(element6.getChildren("InstrumentInfo"));
            }
            boolean bl2 = false;
            object3 = new HashMap();
            for (n = arrayList5.size() - 1; n >= 0; --n) {
                String string8;
                string4 = (Element)arrayList5.get(n);
                string3 = XMLUtil.getAttr((Element)string4, (String)"action", (String)"ignore");
                if (string3.equals("ignore")) continue;
                n2 = ProjectResources.loadInstrumentElement((Element)string4);
                string2 = (BrokerDto)hashMap2.get(((InstrumentInfo)n2).broker);
                object2 = string2 == null ? BrokerManager.getInstance().getDefaultBroker() : BrokerManager.getInstance().getBroker(string2.getName());
                object = object2.getId();
                string = string4.getAttributeValue("instrument");
                if (string3.equals("add")) {
                    ((InstrumentInfo)n2).instrument = string8 = ProjectResources.generateNewInstrumentName(string);
                    ((InstrumentInfo)n2).broker = (Integer)object;
                    InstrumentManager.addInstrument((InstrumentInfo)n2);
                    bl2 = true;
                    object3.put(string, string8);
                    continue;
                }
                if (string3.equals("replace")) {
                    string8 = string4.getAttributeValue("replaceInstrument");
                    if (!InstrumentManager.checkInstrumentExists((String)string8)) {
                        throw new Exception(L.t((String)"Replace instrument '%s' doesn't exist", (Object[])new Object[]{string8}));
                    }
                    object3.put(string, string8);
                    continue;
                }
                throw new Exception(L.t((String)"Unknown instrument action '%s'", (Object[])new Object[]{string3}));
            }
            symbolsToClone.clear();
            n = 0;
            boolean bl3 = true;
            for (int i = arrayList.size() - 1; i >= 0; --i) {
                String string9;
                String string10;
                int n3;
                String string11;
                n2 = (Element)arrayList.get(i);
                string2 = XMLUtil.getAttr((Element)n2, (String)"action", (String)"ignore");
                if (string2.equals("ignore")) continue;
                object2 = n2.getAttributeValue("name");
                if (string2.equals("replace")) {
                    object = n2.getAttributeValue("replaceSymbol");
                    if (!DataManager.checkDataExists((String)"History", (String)object)) {
                        throw new Exception(L.t((String)"Replace symbol '%s' doesn't exist", (Object[])new Object[]{object}));
                    }
                    string = DataManager.getDataInfo((String)"History", (String)object);
                    ProjectResources.replaceSetupSymbols(arrayList2, (String)object2, (DataInfo)string);
                    ProjectResources.replaceDatasSymbols(element3, (String)object2, (DataInfo)string);
                    continue;
                }
                object = XMLUtil.getChildElem((Element)n2, (String)"InstrumentInfo");
                string = new InstrumentInfo((Element)object);
                if (((InstrumentInfo)string).broker != -1 && (string11 = (String)object3.get(((InstrumentInfo)string).instrument)) != null && InstrumentManager.checkInstrumentExists((String)string11)) {
                    string = InstrumentManager.getInstrumentInfo((String)string11);
                }
                if ((n3 = XMLUtil.getIntAttr((Element)n2, (String)"broker", (int)-1)) != -1) {
                    BrokerDto brokerDto = (BrokerDto)hashMap2.get(n3);
                    BrokerDto brokerDto2 = brokerDto == null ? BrokerManager.getInstance().getDefaultBroker() : BrokerManager.getInstance().getBroker(brokerDto.getName());
                    n3 = brokerDto2.getId();
                }
                int n4 = XMLUtil.getIntAttr((Element)n2, (String)"barType");
                int n5 = XMLUtil.getIntAttr((Element)n2, (String)"source");
                String string12 = n2.getAttributeValue("precision");
                String string13 = n2.getAttributeValue("uSymbol");
                String string14 = n2.getAttributeValue("uSymbolName");
                long l = XMLUtil.getLongAttr((Element)n2, (String)"dateFrom");
                long l2 = XMLUtil.getLongAttr((Element)n2, (String)"dateTo");
                String string15 = n2.getAttributeValue("timezone");
                String string16 = n2.getAttributeValue("cloneFrom");
                String string17 = n2.getAttributeValue("sourceTimezone");
                boolean bl4 = XMLUtil.getBooleanAttr((Element)n2, (String)"removeWeekends", (boolean)false);
                if (string2.equals("add")) {
                    DataInfo dataInfo;
                    string10 = ProjectResources.checkInstrumentExists((InstrumentInfo)string);
                    string9 = ProjectResources.generateNewSymbolName((String)object2);
                    String string18 = null;
                    if (string16 != null) {
                        if (!DataManager.checkDataExists((String)"History", (String)string16)) {
                            DataManager.addData((String)"History", (String)string16, (String)string10, (int)n4, (int)n5, (String)string13, (String)string14, (int)-1, (int)n3);
                            DataManager.updateData((String)"History", (String)string16, (long)0L, (long)0L, (int)0, (long)0L, (int)n4, (String)string12, (String)string17);
                            symbolsToClone.add(new CloneInfo(string9, string16, string15, bl4));
                            string18 = string16;
                        } else {
                            dataInfo = DataManager.getDataInfo((String)"History", (String)string16);
                            if (dataInfo.source != n5 || dataInfo.barTimeType != n4 || dataInfo.timeframe == null || !dataInfo.timeframe.equals(string12) || !ProjectResources.compareInstruments(dataInfo.symbolInfo, (InstrumentInfo)string)) {
                                String string19 = ProjectResources.generateNewSymbolName(string16);
                                DataManager.addData((String)"History", (String)string19, (String)string10, (int)n4, (int)n5, (String)string13, (String)string14, (int)-1, (int)n3);
                                DataManager.updateData((String)"History", (String)string19, (long)0L, (long)0L, (int)0, (long)0L, (int)n4, (String)string12, (String)string17);
                                symbolsToClone.add(new CloneInfo(string9, string19, string15, bl4));
                                string18 = string19;
                            } else {
                                symbolsToClone.add(new CloneInfo(string9, string16, string15, bl4));
                                string18 = string16;
                            }
                        }
                    }
                    jSONArray.put((Object)new JSONObject().put("originalName", object2).put("createdName", (Object)string9));
                    if (DataManager.isGroupAlias((String)object2)) {
                        dataInfo = new BasketDto();
                        dataInfo.setName((String)object2);
                        dataInfo.setDesc(n2.getAttributeValue("groupDescription"));
                        BasketOfStocksManager.getInstance().saveGroup((BasketDto)dataInfo);
                        SQWebSocketManager.addToDataQueue(WSDataObjects.getBaskets(), "SQUANT", "QDM");
                    } else {
                        DataManager.addData((String)"History", (String)string9, (String)string10, (int)n4, (int)n5, (String)(string16 != null ? string18 : string13), (String)(string16 != null ? string18 : string14), (int)-1, (int)n3);
                        if (string16 != null) {
                            dataInfo = DataManager.getDataInfo((String)"History", (String)string18);
                            DataManager.updateData((String)"History", (String)string9, (long)0L, (long)0L, (int)0, (long)0L, (int)n4, (String)string12, (String)string15, (int)dataInfo.id, (boolean)bl4);
                        } else {
                            DataManager.updateData((String)"History", (String)string9, (long)0L, (long)0L, (int)0, (long)0L, (int)n4, (String)string12, (String)string15);
                        }
                    }
                    if (!string9.equals(object2)) {
                        dataInfo = DataManager.getDataInfo((String)"History", (String)string9);
                        ProjectResources.replaceSetupSymbols(arrayList2, (String)object2, dataInfo);
                        ProjectResources.replaceDatasSymbols(element3, (String)object2, dataInfo);
                    }
                    n = 1;
                    bl3 = false;
                } else if (string2.equals("overwrite")) {
                    string10 = ProjectResources.checkInstrumentExists((InstrumentInfo)string);
                    string9 = DataManager.getDataInfo((String)"History", (String)object2);
                    DataManager.updateData((String)"History", (String)object2, (long)0L, (long)0L, (int)0, (long)0L, (int)n4, (String)string12, (String)string15, (int)((DataInfo)string9).sourceDataId, (boolean)bl4);
                    DataManager.updateInstrument((String)"History", (String)object2, (String)string10);
                    n = 1;
                    bl3 = false;
                } else if (string2.equals("download")) {
                    n = 1;
                    bl3 = false;
                } else {
                    throw new Exception(L.t((String)"Unknown symbol action '%s'", (Object[])new Object[]{string2}));
                }
                object4 = (String)object4 + (((String)object4).isEmpty() ? "" : ",") + (String)object2;
                string52 = string52 + (string52.isEmpty() ? "" : ",") + string13;
                string6 = string6 + (string6.isEmpty() ? "" : ",") + SQTime.formatDate((long)l);
                string7 = string7 + (string7.isEmpty() ? "" : ",") + SQTime.formatDate((long)l2);
            }
            if (bl) {
                SQWebSocketManager.addToDataQueue(WSDataObjects.getBrokers(), "SQUANT", "QDM");
            }
            if (n != 0 || bl2) {
                SQWebSocketManager.addToDataQueue(WSDataObjects.getData(null, null), "SQUANT", "QDM");
                SQWebSocketManager.addToDataQueue(WSDataObjects.getInstruments(), "SQUANT", "QDM");
            }
            ArrayList arrayList6 = new ArrayList();
            if (element5 != null) {
                arrayList6.addAll(element5.getChildren("Session"));
            }
            boolean bl5 = false;
            for (int i = arrayList6.size() - 1; i >= 0; --i) {
                String string20;
                object2 = (Element)arrayList6.get(i);
                object = XMLUtil.getAttr((Element)object2, (String)"action", (String)"ignore");
                if (object == null || ((String)object).isEmpty() || ((String)object).equals("ignore")) continue;
                string = object2.getAttributeValue("name");
                ArrayList<SessionElement> arrayList7 = ProjectResources.loadSessionElements((Element)object2);
                if (((String)object).equals("add")) {
                    string20 = ProjectResources.generateNewSessionName(string);
                    SessionManager.addSession((Session)new Session(string20, arrayList7));
                    if (!string20.equals(string)) {
                        ProjectResources.replaceSetupSessions(arrayList2, string, string20);
                    }
                    bl5 = true;
                    continue;
                }
                if (((String)object).equals("overwrite")) {
                    SessionManager.updateSession((String)string, arrayList7);
                    bl5 = true;
                    continue;
                }
                if (((String)object).equals("replace")) {
                    string20 = object2.getAttributeValue("replaceSession");
                    if (!SessionManager.checkSessionExists((String)string20)) {
                        throw new Exception(L.t((String)"Replace session '%s' doesn't exist", (Object[])new Object[]{string20}));
                    }
                    ProjectResources.replaceSetupSessions(arrayList2, string, string20);
                    continue;
                }
                throw new Exception(L.t((String)"Unknown session action '%s'", (Object[])new Object[]{object}));
            }
            ProjectResources.cloneSymbols();
            if (bl5) {
                SQWebSocketManager.addToDataQueue(WSDataObjects.getSessions(), "SQUANT", "QDM");
            }
            return bl3;
        }
        catch (Exception exception) {
            Log.error("Cannot resolve resources", (Throwable)exception);
            throw new Exception("Cannot resolve resources - " + exception.getMessage());
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void cancelImport() {
        DownloadDispatcher.get().removeExtraListener(listener);
        long l = lock.readLock();
        try {
            for (int i = 0; i < symbolsToDownload.size(); ++i) {
                String string = symbolsToDownload.get(i);
                DownloadDispatcher.get().stop(string);
            }
        }
        finally {
            lock.unlock(l);
        }
        dataCloner.cancel();
    }

    public static String checkInstrumentExists(InstrumentInfo instrumentInfo) throws Exception {
        String string = instrumentInfo.instrument;
        if (!InstrumentManager.checkInstrumentExists((String)instrumentInfo.instrument)) {
            InstrumentManager.addInstrument((InstrumentInfo)instrumentInfo);
        } else {
            InstrumentInfo instrumentInfo2 = InstrumentManager.getInstrumentInfo((String)instrumentInfo.instrument);
            if (!ProjectResources.compareInstruments(instrumentInfo2, instrumentInfo)) {
                int n = 2;
                string = String.format("%s(%d)", instrumentInfo.instrument, n++);
                while (InstrumentManager.checkInstrumentExists((String)string)) {
                    string = String.format("%s(%d)", instrumentInfo.instrument, n++);
                }
                instrumentInfo.instrument = string;
                InstrumentManager.addInstrument((InstrumentInfo)instrumentInfo);
            }
        }
        return string;
    }

    private static String generateNewSymbolName(String string) {
        String string2 = string;
        int n = 2;
        while (DataManager.checkDataExists((String)"History", (String)string2)) {
            string2 = String.format("%s(%d)", string, n++);
        }
        return string2;
    }

    private static String generateNewSessionName(String string) {
        String string2 = string;
        int n = 2;
        while (SessionManager.checkSessionExists((String)string2)) {
            string2 = String.format("%s(%d)", string, n++);
        }
        return string2;
    }

    private static String generateNewBrokerName(String string) {
        String string2 = string = string.replace("[", "").replace("]", "");
        int n = 2;
        while (BrokerManager.getInstance().getBroker("[" + string2 + "]") != null) {
            string2 = String.format("%s(%d)", string, n++);
        }
        return "[" + string2 + "]";
    }

    private static String generateNewInstrumentName(String string) {
        String string2 = string;
        int n = 2;
        while (InstrumentManager.checkInstrumentExists((String)string2)) {
            string2 = String.format("%s(%d)", string, n++);
        }
        return string2;
    }

    private static ArrayList<SessionElement> loadSessionElements(Element element) throws Exception {
        ArrayList<SessionElement> arrayList = new ArrayList<SessionElement>();
        List list = element.getChildren("Element");
        for (int i = 0; i < list.size(); ++i) {
            Element element2 = (Element)list.get(i);
            String string = element2.getAttributeValue("dayFrom");
            String string2 = element2.getAttributeValue("dayTo");
            String string3 = element2.getAttributeValue("timeFrom");
            String string4 = element2.getAttributeValue("timeTo");
            boolean bl = XMLUtil.getBooleanAttr((Element)element2, (String)"eod");
            arrayList.add(new SessionElement(string, string3, string2, string4, bl));
        }
        return arrayList;
    }

    public static BrokerDto loadBrokerElement(Element element) {
        BrokerDto brokerDto = new BrokerDto();
        brokerDto.setId(Integer.valueOf(element.getAttributeValue("id")));
        brokerDto.setName(element.getAttributeValue("name"));
        brokerDto.setPostfix(element.getAttributeValue("postfix"));
        brokerDto.setDesc(element.getAttributeValue("description"));
        brokerDto.setMtTimezone(element.getAttributeValue("timezone"));
        brokerDto.setMtUse(Boolean.valueOf(element.getAttributeValue("mtUse")).booleanValue());
        brokerDto.setStockPickerUse(Boolean.valueOf(element.getAttributeValue("spUse")).booleanValue());
        return brokerDto;
    }

    private static InstrumentInfo loadInstrumentElement(Element element) {
        InstrumentInfo instrumentInfo = new InstrumentInfo(element);
        return instrumentInfo;
    }

    private static Element createSymbolElement(DataInfo dataInfo, long l, long l2) throws Exception {
        Element element = new Element("Symbol");
        element.setAttribute("name", dataInfo.symbol);
        element.setAttribute("source", String.valueOf(dataInfo.source));
        element.setAttribute("barType", String.valueOf(dataInfo.barTimeType));
        element.setAttribute("precision", dataInfo.timeframe);
        element.setAttribute("timezone", dataInfo.timezone != null ? dataInfo.timezone : "Etc/UCT");
        element.setAttribute("dateFrom", String.valueOf(l > 0L ? l : dataInfo.dateFrom));
        element.setAttribute("dateTo", String.valueOf(l2 > 0L ? l2 : dataInfo.dateTo));
        element.setAttribute("uSymbol", dataInfo.uSymbol != null ? dataInfo.uSymbol : "");
        element.setAttribute("uSymbolName", dataInfo.uSymbolName != null ? dataInfo.uSymbolName : "");
        element.setAttribute("removeWeekends", String.valueOf(dataInfo.removeWeekends));
        if (DataManager.isGroupAlias((String)dataInfo.symbol)) {
            String string = "";
            for (BasketDto basketDto : BasketOfStocksManager.getInstance().getGroups()) {
                if (!basketDto.getName().equals(dataInfo.symbol)) continue;
                string = basketDto.getDesc() != null ? basketDto.getDesc() : "";
                break;
            }
            element.setAttribute("groupDescription", string);
        }
        element.setAttribute("broker", String.valueOf(dataInfo.brokerId));
        element.addContent((Content)dataInfo.symbolInfo.getXML());
        return element;
    }

    private static Element createSessionElement(String string) throws Exception {
        Session session = SessionManager.getSession((String)string);
        if (session == null) {
            throw new Exception(String.format("Session '%s' doesn't exist", string));
        }
        Element element = session.getXML();
        if (element == null) {
            throw new Exception(String.format("Failed to convert session '%s' to xml.", string));
        }
        return element;
    }

    private static boolean compareInstruments(InstrumentInfo instrumentInfo, InstrumentInfo instrumentInfo2) {
        if (instrumentInfo == null || instrumentInfo2 == null) {
            return true;
        }
        return instrumentInfo.dataType == instrumentInfo2.dataType && instrumentInfo.pointValue == instrumentInfo2.pointValue && instrumentInfo.tickSize == instrumentInfo2.tickSize && instrumentInfo.tickStep == instrumentInfo2.tickStep && instrumentInfo.tickValueInMoney == instrumentInfo2.tickValueInMoney;
    }

    private static void replaceDatasSymbols(Element element, String string, DataInfo dataInfo) {
        if (element == null) {
            return;
        }
        try {
            Element element2 = element.getChild("Strategy").getChild("Datas");
            if (element2 == null) {
                return;
            }
            for (Element element3 : element2.getChildren("data")) {
                Element element4;
                Element element5 = element3.getChild("id");
                if (element5 != null && "0".equals(element5.getText()) || (element4 = element3.getChild("symbol")) == null || !string.equals(element4.getText())) continue;
                element4.setText(dataInfo.symbol);
            }
        }
        catch (Exception exception) {
            Log.error("Updating Datas symbols failed", (Throwable)exception);
        }
    }

    private static void replaceSetupSymbols(ArrayList<Element> arrayList, String string, DataInfo dataInfo) throws Exception {
        Object object;
        Element element;
        Element element2;
        int n;
        ArrayList<Element> arrayList2 = ProjectResources.getSettingsElements(arrayList);
        ArrayList arrayList3 = new ArrayList();
        for (n = 0; n < arrayList2.size(); ++n) {
            element2 = arrayList2.get(n);
            Element element3 = element2.getChild("Data");
            if (element3 == null || (element = element3.getChild("Setups")) == null) continue;
            arrayList3.addAll(element.getChildren("Setup"));
        }
        for (n = 0; n < arrayList3.size(); ++n) {
            element2 = (Element)arrayList3.get(n);
            long l = XMLUtil.parseDate((String)element2.getAttributeValue("dateFrom"));
            long l2 = XMLUtil.parseDate((String)element2.getAttributeValue("dateTo"));
            List list = element2.getChildren("Chart");
            for (int i = 0; i < list.size(); ++i) {
                Element element4;
                Element element5 = (Element)list.get(i);
                String string2 = element5.getAttributeValue("symbol");
                if (string2 == null || !string2.equals(string)) continue;
                element5.setAttribute("symbol", dataInfo.symbol);
                if (i != 0) continue;
                element5.setAttribute("spread", dataInfo.symbolInfo.defaultSpread + "");
                element2.setAttribute("slippage", dataInfo.symbolInfo.defaultSlippage + "");
                try {
                    element4 = XMLUtil.stringToElement((String)dataInfo.symbolInfo.commissions);
                    element2.getChild("Commissions").removeContent();
                    element2.getChild("Commissions").addContent((Content)element4);
                }
                catch (Exception exception) {
                    Log.error(L.t((String)"Error while applying default commission.", (Object[])new Object[0]) + " " + exception.getMessage(), (Throwable)exception);
                }
                try {
                    if (dataInfo.symbolInfo.swap != null) {
                        element4 = XMLUtil.stringToElement((String)dataInfo.symbolInfo.swap);
                        element2.removeChild("Swap");
                        element2.addContent((Content)element4);
                    }
                }
                catch (Exception exception) {
                    Log.error(L.t((String)"Error while applying default swap.", (Object[])new Object[0]) + " " + exception.getMessage(), (Throwable)exception);
                }
                long l3 = l;
                long l4 = l2;
                if (l3 < dataInfo.dateFrom) {
                    l3 = dataInfo.dateFrom;
                }
                if (l4 > dataInfo.dateTo) {
                    l4 = dataInfo.dateTo;
                }
                if (l3 > l4) {
                    l3 = dataInfo.dateFrom;
                    l4 = dataInfo.dateTo;
                }
                element2.setAttribute("dateFrom", SQTime.formatDate((long)l3));
                element2.setAttribute("dateTo", SQTime.formatDate((long)l4));
            }
        }
        arrayList3.clear();
        for (n = 0; n < arrayList2.size(); ++n) {
            Element element6;
            element2 = arrayList2.get(n);
            Element element7 = element2.getChild("CrossChecks");
            if (element7 == null || (element = element7.getChild("RetestOnAdditionalMarkets")) == null || (element6 = element.getChild("Settings")) == null || (object = element6.getChild("Setups")) == null) continue;
            arrayList3.addAll(object.getChildren("Setup"));
        }
        for (n = 0; n < arrayList3.size(); ++n) {
            element2 = (Element)arrayList3.get(n);
            List list = element2.getChildren("Chart");
            for (int i = 0; i < list.size(); ++i) {
                Element element8 = (Element)list.get(i);
                object = element8.getAttributeValue("symbol");
                if (object == null || !((String)object).equals(string)) continue;
                element8.setAttribute("symbol", dataInfo.symbol);
            }
        }
    }

    private static void replaceSetupSessions(ArrayList<Element> arrayList, String string, String string2) throws Exception {
        Object object;
        Element element;
        int n;
        ArrayList<Element> arrayList2 = ProjectResources.getSettingsElements(arrayList);
        ArrayList arrayList3 = new ArrayList();
        block0: for (n = 0; n < arrayList2.size(); ++n) {
            Element element2;
            Element element3;
            Element element4;
            Element element5;
            element = arrayList2.get(n);
            object = element.getChild("Data");
            if (object != null && (element5 = object.getChild("Setups")) != null) {
                arrayList3.addAll(element5.getChildren("Setup"));
            }
            if ((element5 = element.getChild("CrossChecks")) != null && (element4 = element5.getChild("RetestOnAdditionalMarkets")) != null && (element3 = element4.getChild("Settings")) != null && (element2 = element3.getChild("Setups")) != null) {
                arrayList3.addAll(element2.getChildren("Setup"));
            }
            if ((element4 = element.getChild("Options")) == null || (element3 = element4.getChild("BuildTradingOptions")) == null || (element2 = element3.getChild("Params")) == null) continue;
            List list = element2.getChildren("Param");
            for (int i = 0; i < list.size(); ++i) {
                Element element6 = (Element)list.get(i);
                String string3 = element6.getAttributeValue("key");
                String string4 = element6.getText();
                if (string3 == null || !string3.equals("Session") || string4 == null || !string4.endsWith(string)) continue;
                element6.setText(string2);
                continue block0;
            }
        }
        for (n = 0; n < arrayList3.size(); ++n) {
            element = (Element)arrayList3.get(n);
            object = element.getAttributeValue("session");
            if (object == null || !((String)object).equals(string)) continue;
            element.setAttribute("session", string2);
        }
    }

    private static ArrayList<Element> getSettingsElements(ArrayList<Element> arrayList) throws Exception {
        ArrayList<Element> arrayList2 = new ArrayList<Element>();
        for (int i = 0; i < arrayList.size(); ++i) {
            Element element;
            Element element2 = arrayList.get(i);
            String string = element2.getName();
            if (string.equals("Project")) {
                element = element2.getChild("Tasks");
                if (element == null) {
                    return arrayList2;
                }
                List list = element.getChildren("Task");
                for (int j = 0; j < list.size(); ++j) {
                    Element element3 = ((Element)list.get(j)).getChild("Settings");
                    if (element3 == null) continue;
                    arrayList2.add(element3);
                }
                continue;
            }
            if (string.equals("Task")) {
                element = element2.getChild("Settings");
                if (element == null) {
                    return arrayList2;
                }
                arrayList2.add(element);
                continue;
            }
            if (string.equals("Settings")) {
                arrayList2.add(element2);
                continue;
            }
            throw new Exception("Invalid XML config. Expected Project/Task/Settings, but got " + string);
        }
        return arrayList2;
    }

    private static void cloneSymbols() {
        ArrayList<CloneInfo> arrayList = new ArrayList<CloneInfo>(symbolsToClone);
        for (int i = 0; i < arrayList.size(); ++i) {
            final CloneInfo cloneInfo = arrayList.get(i);
            dataCloner.cloneToTimezone(cloneInfo.sourceSymbol, cloneInfo.symbol, cloneInfo.timezone, 0, cloneInfo.removeWeekends, null, new IProgressListener(){

                public void onStart() {
                }

                public void onProgress(double d) {
                    System.out.println("Symbol '" + cloneInfo.symbol + "' - progress: " + d);
                }

                public void onPause() {
                }

                public void onContinue() {
                }

                /*
                 * WARNING - Removed try catching itself - possible behaviour change.
                 */
                public void onFinish() {
                    long l = lock.writeLock();
                    try {
                        for (int i = 0; i < symbolsToClone.size(); ++i) {
                            if (!((CloneInfo)symbolsToClone.get((int)i)).symbol.equals(cloneInfo.symbol)) continue;
                            symbolsToClone.remove(i);
                            break;
                        }
                        if (symbolsToClone.isEmpty()) {
                            try {
                                ProjectResources.sendInfoMessage("Project import finished");
                            }
                            catch (Exception exception) {
                                Log.error("Project import failed", (Throwable)exception);
                                ProjectResources.sendErrorMessage("Project import failed - " + exception.getMessage());
                            }
                        }
                    }
                    catch (Exception exception) {
                        Log.error("Project import failed", (Throwable)exception);
                        ProjectResources.sendErrorMessage("Project import failed - " + exception.getMessage());
                    }
                    finally {
                        lock.unlock(l);
                    }
                }

                public void onError(String string) {
                    String string2 = "Project import failed while cloning symbol '" + cloneInfo.symbol + "' to another timeframe - " + string;
                    Log.error(string2);
                    ProjectResources.sendErrorMessage(string2);
                }

                public void onConfirm(String string) {
                }

                public void setMessage(String string) {
                }

                public void setStep(int n) {
                }
            });
        }
    }

    private static void sendInfoMessage(String string) {
        statusData.getDataObject().put("info", (Object)string);
        statusData.getDataObject().remove("error");
        SQWebSocketManager.addToDataQueue(statusData, "TASKMANAGER");
    }

    private static void sendErrorMessage(String string) {
        statusData.getDataObject().put("error", (Object)string);
        SQWebSocketManager.addToDataQueue(statusData, "TASKMANAGER");
    }

    public static class CloneInfo {
        public String symbol;
        public String sourceSymbol;
        public String timezone;
        public boolean removeWeekends;

        public CloneInfo(String string, String string2, String string3, boolean bl) {
            this.symbol = string;
            this.sourceSymbol = string2;
            this.timezone = string3;
            this.removeWeekends = bl;
        }
    }
}

