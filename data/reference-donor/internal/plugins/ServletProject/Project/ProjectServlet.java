/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.hw.OperatingSystem
 *  com.strategyquant.lib.memory.MemoryUsageChecker
 *  com.strategyquant.lib.memory.SQMemoryProtectionError
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.CustomAnalysisMethod
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.DatabankColumn
 *  com.strategyquant.tradinglib.ProjectRunInfo
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategiesActionCache
 *  com.strategyquant.tradinglib.applyMassConfig.ApplyMassConfig
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo
 *  com.strategyquant.tradinglib.customanalysis.CustomAnalysisMethodsList
 *  com.strategyquant.tradinglib.databank.DatabankColumns
 *  com.strategyquant.tradinglib.databank.DatabankTableColumnEntry
 *  com.strategyquant.tradinglib.databank.DefaultDatabankFilter
 *  com.strategyquant.tradinglib.databank.IDatabankFilter
 *  com.strategyquant.tradinglib.databank.IProgressListener
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.file.SQFileManager
 *  com.strategyquant.tradinglib.project.DefaultProjectConfig
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectCustomResources
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.console.CLILogger
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WebSocketNotification
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.strategy.DataItemsGenerator
 *  com.strategyquant.tradinglib.strategy.StrategyLoader
 *  com.strategyquant.tradinglib.strategy.StrategyMerger
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.output.Format
 *  org.jdom2.output.XMLOutputter
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Project;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.hw.OperatingSystem;
import com.strategyquant.lib.memory.MemoryUsageChecker;
import com.strategyquant.lib.memory.SQMemoryProtectionError;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.plugin.Servlet.impl.Project.TaskConfigWorker;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.CustomAnalysisMethod;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.ProjectRunInfo;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategiesActionCache;
import com.strategyquant.tradinglib.applyMassConfig.ApplyMassConfig;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisInfo;
import com.strategyquant.tradinglib.customanalysis.CustomAnalysisMethodsList;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.databank.DatabankTableColumnEntry;
import com.strategyquant.tradinglib.databank.DefaultDatabankFilter;
import com.strategyquant.tradinglib.databank.IDatabankFilter;
import com.strategyquant.tradinglib.databank.IProgressListener;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.project.DefaultProjectConfig;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectCustomResources;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.strategy.DataItemsGenerator;
import com.strategyquant.tradinglib.strategy.StrategyLoader;
import com.strategyquant.tradinglib.strategy.StrategyMerger;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.BufferedOutputStream;
import java.io.BufferedWriter;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Writer;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.jar.Attributes;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.jar.Manifest;
import java.util.stream.Collectors;
import java.util.zip.ZipOutputStream;
import org.jdom2.Content;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.output.Format;
import org.jdom2.output.XMLOutputter;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProjectServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ProjectServlet.class);
    private static final String ApplyMassConfigPath = SQPaths.settingsDirPath + "/ApplyMassConfig.xml";
    private static final String LockCustomAnalysis = "CustomAnalysisManual";
    private OperatingSystem os = new OperatingSystem();

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "start": {
                return this.onStart(args);
            }
            case "pause": {
                return this.onPause(args);
            }
            case "stop": {
                return this.onStop(args);
            }
            case "resume": {
                return this.onResume(args);
            }
            case "projectChanged": {
                return this.onProjectChanged(args);
            }
            case "databankList": {
                return this.onDatabankList(args);
            }
            case "databankCount": {
                return this.onDatabankCount(args);
            }
            case "listStrategies": {
                return this.onListStrategies(args);
            }
            case "getStrategyStats": {
                return this.onGetStrategyStats(args);
            }
            case "moveDatabank": {
                return this.onMoveDatabank(args);
            }
            case "moveDatabankToPosition": {
                return this.onMoveDatabankToPosition(args);
            }
            case "createDatabank": {
                return this.onCreateDatabank(args);
            }
            case "removeDatabank": {
                return this.onRemoveDatabank(args);
            }
            case "renameDatabank": {
                return this.onRenameDatabank(args);
            }
            case "loadFilesToDatabank": {
                return this.onLoadFilesToDatabank(args);
            }
            case "saveReports": {
                return this.onSaveReports(args);
            }
            case "saveSingleFileJava": {
                return this.onSaveSingleFileJava(args);
            }
            case "removeReports": {
                return this.onRemoveReports(args);
            }
            case "createPortfolio": {
                return this.onCreatePortfolio(args);
            }
            case "removeAllReports": {
                return this.onRemoveAllReports(args);
            }
            case "clearAllDatabanks": {
                return this.onClearAllDatabanks(args);
            }
            case "cancelRecordsLoading": {
                return this.onCancelRecordsLoading(args);
            }
            case "getDataItems": {
                return this.onGetDataItems(args);
            }
            case "getRankColumns": {
                return this.onGetRankColumns(args);
            }
            case "changeMaxRecords": {
                return this.onChangeMaxRecords(args);
            }
            case "getXMLConfig": 
            case "getConfig": {
                return this.onGetConfig(args);
            }
            case "checkResources": {
                return this.onCheckResources(args);
            }
            case "updateTaskXML": {
                return this.onUpdateTaskXML(args);
            }
            case "updateProjectXML": {
                return this.onUpdateProjectXML(args);
            }
            case "getTemplateConfig": {
                return this.onGetTemplateConfig(args);
            }
            case "loadConfig": {
                return this.onLoadConfig(args);
            }
            case "saveConfig": {
                return this.onSaveConfig(args);
            }
            case "getCurrentTemplateSettings": {
                return this.onGetCurrentTemplateSettings(args);
            }
            case "updateTemplateConfig": {
                return this.onUpdateTemplateConfig(args);
            }
            case "applySimpleTemplate": {
                return this.onApplySimpleTemplate(args);
            }
            case "resetTaskConfig": {
                return this.onResetTaskConfig(args);
            }
            case "instrumentSelected": {
                return this.onInstrumentSelected(args);
            }
            case "retest": {
                return this.onRetest(args);
            }
            case "confirm": {
                return this.onConfirm(args);
            }
            case "loadGridData": {
                return this.onLoadGridData(args);
            }
            case "setDatabankColumnValue": {
                return this.onSetDatabankColumnValue(args);
            }
            case "setDatabankSynchronization": {
                return this.onSetDatabankSynchronization(args);
            }
            case "synchronizeDatabank": {
                return this.onSynchronizeDatabank(args);
            }
            case "synchronizeDatabanks": {
                return this.onSynchronizeDatabanks(args);
            }
            case "syncfromfiles": {
                return this.onSyncfromfiles(args);
            }
            case "synchronizeAllDatabanks": {
                return this.onSynchronizeAllDatabanks(args);
            }
            case "printToLog": {
                return this.onPrintToLog(args);
            }
            case "cutStrategies": {
                return this.onCutStrategies(args);
            }
            case "copyStrategies": {
                return this.onCopyStrategies(args);
            }
            case "pasteStrategies": {
                return this.onPasteStrategies(args);
            }
            case "resolveResources": {
                return this.onResolveResources(args);
            }
            case "cancelResolving": {
                return this.onCancelResolving();
            }
            case "checkCustomResources": {
                return this.onCheckCustomResources(args);
            }
            case "checkTemplateResources": {
                return this.onCheckTemplateResources(args);
            }
            case "resolveCustomResources": {
                return this.onResolveCustomResources(args);
            }
            case "list": {
                return this.onList();
            }
            case "status": {
                return this.onStatus(args);
            }
            case "mergeStrategies": {
                return this.onMergeStrategies(args);
            }
            case "mergeStrategiesSync": {
                return this.mergeStrategiesSync(args);
            }
            case "splitStrategies": {
                return this.onSplitStrategies(args);
            }
            case "mergeWFStrategies": {
                return this.onMergeWFStrategies(args);
            }
            case "moveStrategiesToPM": {
                return this.onMoveToPM(args);
            }
            case "moveStrategiesToPC": {
                return this.onMoveToPC(args);
            }
            case "applyMassConfig": {
                return this.onApplyMassConfig(args);
            }
            case "applyMassConfigLoad": {
                return this.onApplyMassConfigLoad(args);
            }
            case "runCustomAnalysis": {
                return this.onRunCustomAnalysis(args);
            }
            case "setNote": {
                return this.onSetNote(args);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    private CustomAnalysisInfo getCustomAnalysisInfo(Map<String, String[]> args) throws Exception {
        CustomAnalysisInfo ca = new CustomAnalysisInfo();
        ca.filter = Boolean.valueOf(this.tryGetParamValue(args, "filter"));
        ca.inputArgsPerStrategy1 = this.tryGetParamValue(args, "inputArgsPerStrategy1");
        ca.inputArgsFullDatabank1 = this.tryGetParamValue(args, "inputArgsFullDatabank1");
        String type = this.tryGetParamValue(args, "analyseType");
        String methodType = this.tryGetParamValue(args, "perStrategy1");
        if (!methodType.equals("none") && "strategy".equals(type)) {
            ca.perStrategy1 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(methodType);
        }
        if (!(methodType = this.tryGetParamValue(args, "fullDatabank1")).equals("none") && "databank".equals(type)) {
            ca.fullDatabank1 = (CustomAnalysisMethod)CustomAnalysisMethodsList.get().findClassByName(methodType);
        }
        return ca;
    }

    private String onRunCustomAnalysis(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        CustomAnalysisInfo ca = this.getCustomAnalysisInfo(args);
        String projectName = this.tryGetParam(args, "projectName")[0];
        String databankName = this.tryGetParam(args, "databankName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
        boolean selectedStrategies = Boolean.valueOf(this.tryGetParam(args, "selectedStrategies")[0]);
        ArrayList recordsToAnalyze = databank.getRecords();
        if (selectedStrategies) {
            String[] strategies = this.tryGetParam(args, "strategies[]");
            HashSet<String> strategiesSet = new HashSet<String>(Arrays.asList(strategies));
            ArrayList filteredGroups = new ArrayList();
            for (ResultsGroup resultsGroup : recordsToAnalyze) {
                String name = resultsGroup.getName();
                if (!strategiesSet.contains(name)) continue;
                filteredGroups.add(resultsGroup);
            }
            recordsToAnalyze = filteredGroups;
        }
        String analyseType = this.tryGetParam(args, "analyseType")[0];
        LinkedList<ResultsGroup> forRemove = new LinkedList<ResultsGroup>();
        try {
            if ("strategy".equals(analyseType) && ca.perStrategy1 != null) {
                for (ResultsGroup rg : recordsToAnalyze) {
                    ca.perStrategy1.setInputArgs(ca.inputArgsPerStrategy1);
                    if (ca.perStrategy1.filterStrategy(projectName, "manual", databankName, rg)) continue;
                    forRemove.add(rg);
                }
            }
            if ("databank".equals(analyseType) && ca.fullDatabank1 != null) {
                ca.fullDatabank1.setInputArgs(ca.inputArgsFullDatabank1);
                ArrayList passedResults = ca.fullDatabank1.processDatabank(projectName, "manual", databankName, recordsToAnalyze);
                Set passedNames = passedResults.stream().map(ResultsGroup::getName).collect(Collectors.toSet());
                for (ResultsGroup rg : recordsToAnalyze) {
                    if (passedNames.contains(rg.getName())) continue;
                    forRemove.add(rg);
                }
            }
            if (ca.filter) {
                for (ResultsGroup rg : forRemove) {
                    databank.remove(rg.getName(), true, true, true, true, LockCustomAnalysis);
                }
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Custom analysis failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Custom analysis executed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSetNote(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String note = this.tryGetParam(args, "note")[0];
        String projectName = this.tryGetParam(args, "projectName")[0];
        String databankName = this.tryGetParam(args, "databankName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
        ArrayList<ResultsGroup> records = databank.getRecords();
        String[] strategies = this.tryGetParam(args, "strategies[]");
        HashSet<String> strategiesSet = new HashSet<String>(Arrays.asList(strategies));
        ArrayList<ResultsGroup> filteredGroups = new ArrayList<ResultsGroup>();
        for (ResultsGroup resultsGroup : records) {
            String name = resultsGroup.getName();
            if (!strategiesSet.contains(name)) continue;
            filteredGroups.add(resultsGroup);
        }
        records = filteredGroups;
        try {
            for (ResultsGroup rg : records) {
                rg.setNote(note);
                databank.update(rg.getName(), rg, true, "setNote");
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Set note failed.", (Object[])new Object[0]), (Throwable)e);
        }
        databank.refreshGrid();
        response.put("success", (Object)L.t((String)"Set note executed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onApplyMassConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            Element elApplyMassConfig = XMLUtil.stringToElement((String)xmlConfig);
            XMLUtil.xmlToFile((Element)elApplyMassConfig, (File)new File(ApplyMassConfigPath));
            ApplyMassConfig applyMassConfig = new ApplyMassConfig();
            applyMassConfig.init(project, elApplyMassConfig);
            applyMassConfig.applyChangesToTasks(project, null);
            SQFileManager.updateWholeProjectConfig((SQProject)project);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot apply mass config.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Mass config applied.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onApplyMassConfigLoad(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            File f = new File(ApplyMassConfigPath);
            Element xmlConfig = f.exists() ? XMLUtil.fileToXmlElement((File)f) : new Element("ApplyMassConfig");
            response.put("xmlConfig", (Object)XMLUtil.elementToString((Element)xmlConfig));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot load last apply mass config.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Mass config loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSynchronizeAllDatabanks(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            List projects = ProjectEngine.list();
            for (SQProject project : projects) {
                ArrayList databanks = project.getDatabanks().list();
                for (Databank databank : databanks) {
                    databank.synchronizeNow(String.format("API request project/synchronizeAllDatabanks %s/%s", project.getName(), databank.getName()));
                }
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot synchronize databanks.", (Object[])new Object[0]), (Throwable)e);
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            response.put("success", (Object)L.t((String)"Synchronization finished.", (Object[])new Object[0]));
        } else {
            response.put("success", (Object)L.t((String)"Synchronization started.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onSynchronizeDatabanks(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        ArrayList databanks = project.getDatabanks().list();
        for (final Databank databank : databanks) {
            try {
                databank.loadStrategies(new IProgressListener(){
                    final /* synthetic */ ProjectServlet this$0;
                    {
                        this.this$0 = this$0;
                    }

                    public void onError(double percent, String error) {
                        CLILogger.log((String)String.format("Loading strategies to databank '%s' failed - %s", databank.getName(), error));
                    }

                    public void onDone() {
                        CLILogger.log((String)String.format("Loaded %d strategies to databank %s", databank.size(), databank.getName()));
                    }

                    public void onProgress(double percentDone) {
                    }
                });
            }
            catch (Exception e) {
                return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot synchronize databank.", (Object[])new Object[0]), (Throwable)e);
            }
        }
        response.put("success", (Object)L.t((String)"Synchronization finished.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDatabankCount(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        Databank db = this.getDatabank(parameterMap);
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            CLILogger.log((String)String.format("Records: %d", db.size()));
        } else {
            response.put("count", db.size());
            response.put("success", (Object)L.t((String)"Databank count retrieved.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onDatabankList(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        JSONArray databanks = this.listDatabanks(project);
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            for (int i = 0; i < databanks.length(); ++i) {
                JSONObject databank = databanks.getJSONObject(i);
                CLILogger.log((String)String.format("%s, Records: %s", databank.getString("name"), databank.getInt("records")));
            }
        } else {
            response.put("databanks", (Object)databanks);
            response.put("success", (Object)L.t((String)"Databanks listed.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onMoveDatabank(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        String databankName = this.tryGetParam(parameterMap, "databankName")[0];
        boolean moveLeft = Boolean.parseBoolean(this.tryGetParam(parameterMap, "moveLeft")[0]);
        SQProject project = ProjectEngine.get((String)projectName);
        project.getDatabanks().move(databankName, moveLeft);
        response.put("databanks", (Object)this.listDatabanks(project));
        response.put("success", (Object)L.t((String)"Databanks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMoveDatabankToPosition(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        String databankName = this.tryGetParam(parameterMap, "databankName")[0];
        int newPosition = Integer.parseInt(this.tryGetParam(parameterMap, "newPosition")[0]);
        SQProject project = ProjectEngine.get((String)projectName);
        project.getDatabanks().moveToPosition(databankName, newPosition);
        response.put("databanks", (Object)this.listDatabanks(project));
        response.put("success", (Object)L.t((String)"Databanks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray listDatabanks(SQProject project) {
        JSONArray array = new JSONArray();
        for (Databank databank : project.getDatabanks().list()) {
            if (databank.getView() == null) {
                databank.setViewByName("Default - Main data");
            }
            JSONObject item = new JSONObject();
            item.put("name", (Object)databank.getName());
            item.put("view", (Object)databank.getView().getName());
            item.put("records", databank.getRecords().size());
            item.put("syncType", (Object)databank.getSyncType());
            item.put("position", databank.getPosition());
            array.put((Object)item);
        }
        return array;
    }

    private String onListStrategies(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        Databank db = this.getDatabank(parameterMap);
        db.setViewByName("Default - Main data");
        JSONArray strategies = new JSONArray();
        for (ResultsGroup rg : db.getRecords()) {
            strategies.put((Object)rg.getName());
        }
        response.put("strategies", (Object)strategies);
        response.put("success", (Object)L.t((String)"Strategies listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetStrategyStats(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        Databank db = this.getDatabank(parameterMap);
        db.setViewByName("Default - Main data");
        String strategyName = this.tryGetParam(parameterMap, "strategyName")[0];
        ArrayList bufferData = db.getBufferData(false);
        ArrayList records = db.getRecords();
        for (int i = 0; i < records.size(); ++i) {
            if (!((ResultsGroup)records.get(i)).getName().equals(strategyName)) continue;
            JSONArray columns = new JSONArray();
            for (DatabankTableColumnEntry col : db.getView().columns) {
                columns.put((Object)col.getColumnEntryName());
            }
            JSONArray values = new JSONArray();
            if (i < bufferData.size()) {
                for (Object v : (Object[])bufferData.get(i)) {
                    values.put((Object)(v != null ? v.toString() : ""));
                }
            }
            response.put("name", (Object)strategyName);
            response.put("columns", (Object)columns);
            response.put("values", (Object)values);
            response.put("success", (Object)L.t((String)"Strategy stats loaded.", (Object[])new Object[0]));
            return response.toString();
        }
        throw new Exception(L.t((String)"Strategy '%s' not found.", (Object[])new Object[]{strategyName}));
    }

    private String onCreateDatabank(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        try {
            SQProject project;
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            String databankName = this.tryGetParam(parameterMap, "databankName")[0];
            boolean predefined = false;
            try {
                predefined = Boolean.parseBoolean(this.tryGetParam(parameterMap, "predefined")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (!predefined) {
                switch (databankName) {
                    case "Results": 
                    case "Strategies to improve": 
                    case "Initial population": 
                    case "Strategies to optimize": 
                    case "Existing portfolio": 
                    case "Simple strategies": {
                        throw new Exception(L.t((String)"Name '%s' is reserved and cannot be used.", (Object[])new Object[]{databankName}));
                    }
                }
            }
            if ((project = ProjectEngine.get((String)projectName)).getDatabanks().get((Object)databankName) != null) {
                throw new Exception(L.t((String)"Databank with name '%s' already exists.", (Object[])new Object[]{databankName}));
            }
            int position = parameterMap.containsKey("position") ? Integer.parseInt(this.tryGetParam(parameterMap, "position")[0]) : project.getDatabanks().size();
            Databank newDatabank = project.addDatabank(databankName, position);
            newDatabank.setSyncType(Databank.getDefaultSyncType());
            response.put("xmlConfig", (Object)XMLUtil.elementToString((Element)project.getConfig()));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot create databank.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Databank added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveDatabank(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            String databankName = this.tryGetParam(parameterMap, "databankName")[0];
            boolean predefined = false;
            try {
                predefined = Boolean.parseBoolean(this.tryGetParam(parameterMap, "predefined")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (!predefined && Databank.isDefault((String)databankName)) {
                throw new Exception(L.t((String)"You can remove custom databanks only.", (Object[])new Object[0]));
            }
            SQProject project = ProjectEngine.get((String)projectName);
            project.removeDatabank(databankName);
            response.put("xmlConfig", (Object)XMLUtil.elementToString((Element)project.getConfig()));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Databank cannot be removed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Databank removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRenameDatabank(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        String databankName = this.tryGetParam(parameterMap, "databankName")[0];
        String newName = this.tryGetParam(parameterMap, "newName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        if (project.getDatabanks().get((Object)newName) != null) {
            throw new Exception(L.t((String)"Databank with name '%s' already exists.", (Object[])new Object[]{newName}));
        }
        project.getDatabanks().rename(databankName, newName);
        Element elProject = project.getConfig();
        ArrayList tasks = project.getTasks();
        for (int a = 0; a < tasks.size(); ++a) {
            Element elDatabanks;
            ISQTask task = (ISQTask)tasks.get(a);
            Element elSettings = task.getConfig();
            if (elSettings == null || (elDatabanks = elSettings.getChild("Databanks")) == null) continue;
            List databankElems = elDatabanks.getChildren("Databank");
            for (int i = 0; i < databankElems.size(); ++i) {
                Element elDatabank = (Element)databankElems.get(i);
                String name = elDatabank.getAttributeValue("value");
                if (!name.equals(databankName)) continue;
                elDatabank.setAttribute("value", newName);
            }
            if (!task.getType().equals("GoToTask")) continue;
            ArrayList conditionElems = XMLUtil.getNestedElements((Element)elSettings, (String)"Condition");
            for (int i = 0; i < conditionElems.size(); ++i) {
                String name;
                Element elLeftSide;
                String name2;
                Element elCondition = (Element)conditionElems.get(i);
                Element elRightSide = elCondition.getChild("Right-Side");
                if (elRightSide != null && elRightSide.getAttribute("databank") != null && (name2 = elRightSide.getAttributeValue("databank")).equals(databankName)) {
                    elRightSide.setAttribute("databank", newName);
                }
                if ((elLeftSide = elCondition.getChild("Left-Side")) == null || elLeftSide.getAttribute("databank") == null || !(name = elLeftSide.getAttributeValue("databank")).equals(databankName)) continue;
                elLeftSide.setAttribute("databank", newName);
            }
        }
        Element elDatabanks = elProject.getChild("Databanks");
        List databankElems = elDatabanks.getChildren("Databank");
        for (int i = 0; i < databankElems.size(); ++i) {
            Element elDatabank = (Element)databankElems.get(i);
            String name = elDatabank.getAttributeValue("name");
            if (!name.equals(databankName)) continue;
            elDatabank.setAttribute("name", newName);
        }
        SQFileManager.updateWholeProjectConfig((SQProject)project);
        response.put("projectConfig", (Object)new JSONObject(project.toJSON()));
        response.put("success", (Object)L.t((String)"Databanks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStart(Map<String, String[]> parameterMap) {
        String projectName;
        JSONObject response = new JSONObject();
        try {
            String action;
            projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            if (project.getRunningStatus() == 1 || project.getRunningStatus() == 2) {
                Log.error("Trying to start project that is already running!");
                throw new Exception(L.t((String)"Project is already running.", (Object[])new Object[0]));
            }
            if (project.hasUnresolvedResources()) {
                Log.error("Trying to start project that has unresolved resources!");
                throw new Exception(L.t((String)"Project has unresolved resources.", (Object[])new Object[0]));
            }
            if (parameterMap.containsKey("projectXML")) {
                String projectXML = this.tryGetParam(parameterMap, "projectXML")[0];
                projectXML = projectXML.replace(",ChikouSpan=4", "");
                String taskXMLFile = null;
                try {
                    taskXMLFile = this.tryGetParam(parameterMap, "taskXMLFile")[0];
                }
                catch (Exception exception) {
                    // empty catch block
                }
                String taskXML = null;
                try {
                    taskXML = this.tryGetParam(parameterMap, "taskXML")[0];
                }
                catch (Exception exception) {
                    // empty catch block
                }
                this.updateProjectXMLBeforeStart(project, projectXML, taskXMLFile, taskXML);
            }
            project.setRunSpecification(0);
            String string = action = parameterMap.containsKey("action") ? parameterMap.get("action")[0] : null;
            if (action != null) {
                String taskName = this.tryGetParamValue(parameterMap, "taskName");
                if (action.equals("runProjectFromHere")) {
                    project.setRunSpecification(50, taskName);
                } else if (action.equals("runThisTaskOnly")) {
                    project.setRunSpecification(100, taskName);
                } else if (action.equals("runFrom") || action.equals("runTask")) {
                    int taskNumber;
                    try {
                        taskNumber = Integer.valueOf(taskName);
                    }
                    catch (Exception e) {
                        throw new Exception(L.t((String)"Task index must be a number.", (Object[])new Object[0]));
                    }
                    if (taskNumber < 1 || taskNumber > project.getTasksCount()) {
                        throw new Exception(L.t((String)"Task index out of range.", (Object[])new Object[0]));
                    }
                    if (action.equals("runFrom")) {
                        project.setRunSpecification(50, project.getTask(taskNumber - 1).getCustomName());
                    } else {
                        project.setRunSpecification(100, project.getTask(taskNumber - 1).getCustomName());
                    }
                } else {
                    Log.error("Invalid run specification. Action: " + action);
                    throw new Exception(L.t((String)"Invalid run specification. Action: %s", (Object[])new Object[]{action}));
                }
            }
            project.initTasksFromConfig();
            project.beforeStart();
            project.start();
        }
        catch (Exception e) {
            Log.error("Exception onStart (2)", (Throwable)e);
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot start project.", (Object[])new Object[0]), (Throwable)e);
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            response.put("success", (Object)(L.t((String)"Project is running on the background. To get project status use", (Object[])new Object[0]) + "\n" + String.format("-project action=status name=%s", projectName)));
        } else {
            response.put("success", (Object)L.t((String)"Project execution started.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private void updateProjectXMLBeforeStart(SQProject project, String projectXML, String taskXMLFile, String taskXML) throws Exception {
        Element elProject = XMLUtil.stringToElement((String)projectXML);
        project.updateConfig(elProject);
        if (taskXMLFile != null) {
            for (int a = 0; a < project.getTasks().size(); ++a) {
                ISQTask task = project.getTask(a);
                if (!task.getTaskXMLFileName().equals(taskXMLFile)) continue;
                Element elSettings = XMLUtil.stringToElement((String)taskXML);
                task.setConfig(elSettings, false, true);
                ProjectResources.addResources((ISQTask)task);
                SQFileManager.updateTaskConfig((File)project.getProjectConfigFile(), (String)taskXMLFile, (Element)task.getConfig());
                break;
            }
        }
        ProjectResources.checkBuildTemplates((SQProject)project);
    }

    private String onResume(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            project.resume();
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resume project.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Project execution resumed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onPause(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            project.pause();
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot pause project.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Project execution paused.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStop(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            project.stop();
        }
        catch (Exception e) {
            Log.error("Exception onStop, running status: {}", (Throwable)e);
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot stop project.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Project execution stopped.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onProjectChanged(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        project.log.resetLastData();
        project.bestResults.resetLastData();
        project.publisher.resetLastData();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onGetRankColumns(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        JSONArray columnsArray = new JSONArray();
        try {
            Databank db = this.getDatabank(args);
            for (DatabankTableColumnEntry columnEntry : db.getView().columns) {
                DatabankColumn column = columnEntry.tableColumn;
                if (column.valueType != 1 && column.valueType != 2) continue;
                columnsArray.put((Object)columnEntry.getColumnEntryName());
            }
            response.put("rankColumns", (Object)columnsArray);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot list rank columns.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Rank columns listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onChangeMaxRecords(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String maxRecords = this.tryGetParam(args, "maxRecords")[0];
            boolean showProgress = false;
            final SQProject project = ProjectEngine.get((String)projectName);
            final Databank databank = this.getDatabank(args);
            try {
                boolean dismissTooSimilarStrategies = false;
                IDatabankFilter existingFilter = databank.getFilter();
                if (existingFilter != null && existingFilter instanceof DefaultDatabankFilter) {
                    dismissTooSimilarStrategies = ((DefaultDatabankFilter)existingFilter).getDismissTooSimilarStrategies();
                }
                DefaultDatabankFilter filter = new DefaultDatabankFilter(Integer.parseInt(maxRecords), dismissTooSimilarStrategies);
                databank.applyFilter((IDatabankFilter)filter, new IProgressListener(){
                    final /* synthetic */ ProjectServlet this$0;
                    {
                        this.this$0 = this$0;
                    }

                    public void onProgress(double percentDone) {
                        project.getProgress().update("max-strategies-change", percentDone, null);
                    }

                    public void onError(double percentDone, String error) {
                        project.getProgress().update("max-strategies-change", percentDone, error);
                    }

                    public void onDone() {
                        databank.removeFilter();
                    }
                });
                response.put("showProgress", showProgress);
            }
            catch (Exception e) {
                if (databank != null) {
                    databank.removeFilter();
                }
                throw e;
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot change max strategies count.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Max strategies setting changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadFilesToDatabank(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParam(parameterMap, "projectName")[0];
        String[] paths = null;
        if (parameterMap.containsKey("folder")) {
            String folder = this.tryGetParam(parameterMap, "folder")[0];
            String strategies = this.getParam(parameterMap, "strategies", "all");
            ArrayList<String> list = new ArrayList<String>();
            File dir = new File(folder);
            if (!dir.isDirectory()) {
                throw new Exception(L.t((String)"'%s' is not a directory.", (Object[])new Object[]{dir.getAbsolutePath()}));
            }
            File[] directoryListing = dir.listFiles();
            if (directoryListing != null) {
                for (File child : directoryListing) {
                    if (!strategies.equals("all") && !strategies.contains(SQUtils.stripExtension((String)child.getName()))) continue;
                    list.add(child.getAbsolutePath());
                }
            }
            paths = list.toArray(new String[list.size()]);
        } else {
            paths = this.tryGetParam(parameterMap, "filePaths[]");
        }
        final SQProject project = ProjectEngine.get((String)projectName);
        final Databank databank = this.getDatabank(parameterMap);
        final boolean clear = parameterMap.containsKey("clear") ? Boolean.parseBoolean(this.tryGetParam(parameterMap, "clear")[0]) : false;
        final String[] p = paths;
        new Thread(this){
            final /* synthetic */ ProjectServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.loadFiles(databank, p, project, clear, "load");
                Log.info("Strategies loaded");
            }
        }.start();
        response.put("success", (Object)L.t((String)"Loading strategies.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void loadFiles(Databank databank, String[] paths, SQProject project, boolean clear, String action) {
        Throwable lastException = null;
        project.bestResults.disable();
        try {
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
                        databank.updateBestResults(resultsGroup);
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
            project.getProgress().update(action, 100.0, lastException == null ? null : "Some strategies were not loaded because of errors.<br>Last error: " + lastException.getMessage());
        }
    }

    private String onInstrumentSelected(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        StrategyLoader.instrumentSelected();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onCancelRecordsLoading(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        StrategyLoader.cancel();
        response.put("success", (Object)L.t((String)"Records loading canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveReports(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            String strategies = this.tryGetParam(parameterMap, "strategies")[0];
            String[] stgs = strategies.split(",");
            SQProject project = ProjectEngine.get((String)projectName);
            Databank databank = this.getDatabank(parameterMap);
            if (stgs.length == 1 && stgs[0].equals("all")) {
                stgs = new String[databank.size()];
                databank.getRecordKeys().toArray(stgs);
            }
            ProjectConfigHelper.delete((SQProject)project, (Databank)databank, (String[])stgs, (String)"onRemoveReports");
            response.put("records", databank.size());
            response.put("success", (Object)L.t((String)"Reports removed.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Removing reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Reports removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveAllReports(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            Databank databank = this.getDatabank(parameterMap);
            databank.removeAll(true, String.format("API request project/removeAllReports from databank %s/%s", projectName, databank.getName()));
            String[] strategies = new String[databank.size()];
            strategies = databank.getRecordKeys().toArray(strategies);
            if (strategies.length == 0) {
                databank.addExtraDatabankChange("remove", "DatabankEmpty");
            } else {
                ProjectConfigHelper.delete((SQProject)project, (Databank)databank, (String[])strategies, (String)"onRemoveAllReports");
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Removing reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Reports removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onClearAllDatabanks(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            for (String databankName : project.getDatabanks().keySet()) {
                Databank databank = (Databank)project.getDatabanks().get((Object)databankName);
                if (databank.getRecords().size() == 0) continue;
                databank.clearRecords(true, true, String.format("API request project/clearAllDatabanks from project %s/%s", projectName, databankName));
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Clearing databanks failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Databanks cleared.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCreatePortfolio(final Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        new Thread(this){
            final /* synthetic */ ProjectServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.createPortfolio(parameterMap);
            }
        }.start();
        response.put("success", (Object)L.t((String)"Creating portfolio started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMergeStrategies(final Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        new Thread(this){
            final /* synthetic */ ProjectServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.mergeStrategiesSync(parameterMap);
            }
        }.start();
        response.put("success", (Object)L.t((String)"Merging strategies started.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSplitStrategies(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        SQProject project = null;
        Databank databank = null;
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            project = ProjectEngine.get((String)projectName);
            String strategies = this.tryGetParam(parameterMap, "strategies")[0];
            String[] stgs = strategies.split(",");
            databank = this.getDatabank(parameterMap);
            if (stgs.length == 1 && stgs[0].equals("all")) {
                stgs = new String[databank.size()];
                databank.getRecordKeys().toArray(stgs);
            }
            project.publisher.resetLastData("progress-channel");
            project.getProgress().update("Split strategies", -1.0, null, L.t((String)"Splitting strategies", (Object[])new Object[0]));
            JSONArray splitNames = new JSONArray();
            for (String strategy : stgs) {
                ResultsGroup rg = databank.getLocked(strategy, "onSplitStrategies");
                try {
                    if (rg.specialValues().containsKey(SpecialValues.IsMergedPortfolio)) {
                        List results = StrategyMerger.getSplitResults((ResultsGroup)rg);
                        for (int a = 0; a < results.size(); ++a) {
                            ResultsGroup splitStrategy = (ResultsGroup)results.get(a);
                            databank.add(splitStrategy, false);
                            splitNames.put((Object)splitStrategy.getName());
                        }
                        continue;
                    }
                    throw new Exception(L.t((String)"Strategy '%s' cannot be split - it is not a merged portfolio", (Object[])new Object[]{strategy}));
                }
                finally {
                    rg.releaseLock("onSplitStrategies");
                }
            }
            databank.refreshGrid();
            project.getProgress().update("Split strategies", 100.0, null);
            WebSocketNotification.sendSuccess((String)L.t((String)"Strategies split successfully", (Object[])new Object[0]), (String[])new String[]{"SQUANT"});
            response.put("strategies", (Object)splitNames);
        }
        catch (Exception e) {
            if (project != null) {
                project.getProgress().update("Split strategies", 100.0, L.t((String)"Splitting strategies failed", (Object[])new Object[0]) + " - " + e.getMessage(), null);
            }
            if (databank != null) {
                databank.refreshGrid();
            }
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Splitting reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Strategies split successfully", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMoveToPM(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            final SQProject srcProject = ProjectEngine.get((String)projectName);
            final Databank srcDatabank = this.getDatabank(args);
            String strategies = this.tryGetParam(args, "strategies")[0];
            final SQProject tgtProject = ProjectEngine.get((String)"PortfolioMaster");
            final Databank tgtDatabank = (Databank)tgtProject.getDatabanks().get((Object)"Simple strategies");
            if (tgtDatabank == null) {
                throw new Exception(String.format("Databank '%s' doesn't exist in project Portfolio Master.", "Simple strategies"));
            }
            boolean allStrategies = false;
            final String[] strategiesArray = strategies.split(",");
            if (strategiesArray.length == 1 && strategiesArray[0].equals("all")) {
                allStrategies = true;
            }
            final boolean takeAllStrategies = allStrategies;
            new Thread(this){
                final /* synthetic */ ProjectServlet this$0;
                {
                    this.this$0 = this$0;
                }

                /*
                 * WARNING - Removed try catching itself - possible behaviour change.
                 */
                @Override
                public void run() {
                    try {
                        Exception lastException = null;
                        tgtProject.bestResults.disable();
                        srcProject.bestResults.disable();
                        tgtProject.publisher.resetLastData("progress-channel");
                        if (takeAllStrategies) {
                            ArrayList records = srcDatabank.getRecordKeys();
                            int count = records.size();
                            for (int i = 0; i < records.size(); ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked((String)records.get(i), "onMoveToPM");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onMoveToPM");
                                    }
                                    tgtDatabank.add(rgCloned, false);
                                    tgtProject.getProgress().update("Move to Portfolio Master", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to PortfolioMaster failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        } else {
                            int count = strategiesArray.length;
                            for (int i = 0; i < strategiesArray.length; ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked(strategiesArray[i], "onMoveToPM");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onMoveToPM");
                                    }
                                    srcDatabank.remove(rgCloned.getName(), true, true, false, false, "onMoveToPM");
                                    tgtDatabank.add(rgCloned, false);
                                    tgtProject.getProgress().update("Move to Portfolio Master", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to PortfolioMaster failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        }
                        srcDatabank.refreshGrid();
                        tgtDatabank.refreshGrid();
                        tgtProject.getProgress().update("Move to Portfolio Master", 100.0, lastException == null ? null : "Some strategies were not loaded because of errors.");
                        srcDatabank.updateBestResults();
                        tgtDatabank.updateBestResults();
                    }
                    catch (Exception e) {
                        Log.error("Moving strategies to PortfolioMaster failed", (Throwable)e);
                        tgtProject.getProgress().update("Move to Portfolio Master", 100.0, "Moving strategies failed. " + e.getMessage());
                    }
                    catch (OutOfMemoryError e) {
                        tgtProject.getProgress().update("Move to Portfolio Master", 100.0, e.getMessage());
                        srcDatabank.refreshGrid();
                        srcDatabank.updateBestResults();
                        tgtDatabank.refreshGrid();
                        tgtDatabank.updateBestResults();
                    }
                    finally {
                        tgtProject.bestResults.enable();
                        srcProject.bestResults.enable();
                    }
                }
            }.start();
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot load strategies to Portfolio Master.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Strategies moved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMoveToPC(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            final SQProject srcProject = ProjectEngine.get((String)projectName);
            final Databank srcDatabank = this.getDatabank(args);
            String strategies = this.tryGetParam(args, "strategies")[0];
            final SQProject tgtProject = ProjectEngine.get((String)"PortfolioComposer");
            final Databank tgtDatabank = (Databank)tgtProject.getDatabanks().get((Object)"Results");
            if (tgtDatabank == null) {
                throw new Exception(String.format("Databank '%s' doesn't exist in project PortfolioComposer.", "Results"));
            }
            boolean allStrategies = false;
            final String[] strategiesArray = strategies.split(",");
            if (strategiesArray.length == 1 && strategiesArray[0].equals("all")) {
                allStrategies = true;
            }
            final boolean takeAllStrategies = allStrategies;
            new Thread(this){
                final /* synthetic */ ProjectServlet this$0;
                {
                    this.this$0 = this$0;
                }

                /*
                 * WARNING - Removed try catching itself - possible behaviour change.
                 */
                @Override
                public void run() {
                    try {
                        Exception lastException = null;
                        tgtProject.bestResults.disable();
                        srcProject.bestResults.disable();
                        tgtProject.publisher.resetLastData("progress-channel");
                        if (takeAllStrategies) {
                            ArrayList records = srcDatabank.getRecordKeys();
                            int count = records.size();
                            for (int i = 0; i < records.size(); ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked((String)records.get(i), "onMoveToPC");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onMoveToPC");
                                    }
                                    tgtDatabank.add(rgCloned, false);
                                    tgtProject.getProgress().update("Move to Portfolio Composer", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to PortfolioComposer failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        } else {
                            int count = strategiesArray.length;
                            for (int i = 0; i < strategiesArray.length; ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked(strategiesArray[i], "onMoveToPC");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onMoveToPC");
                                    }
                                    srcDatabank.remove(rgCloned.getName(), true, true, false, false, "onMoveToPC");
                                    tgtDatabank.add(rgCloned, false);
                                    tgtProject.getProgress().update("Move to Portfolio Composer", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to PortfolioComposer failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        }
                        srcDatabank.refreshGrid();
                        tgtDatabank.refreshGrid();
                        tgtProject.getProgress().update("Move to Portfolio Composer", 100.0, lastException == null ? null : "Some strategies were not loaded because of errors.");
                        srcDatabank.updateBestResults();
                        tgtDatabank.updateBestResults();
                    }
                    catch (Exception e) {
                        Log.error("Moving strategies to PortfolioComposer failed", (Throwable)e);
                        tgtProject.getProgress().update("Move to Portfolio Composer", 100.0, "Moving strategies failed. " + e.getMessage());
                    }
                    catch (OutOfMemoryError e) {
                        tgtProject.getProgress().update("Move to Portfolio Composer", 100.0, e.getMessage());
                        srcDatabank.refreshGrid();
                        srcDatabank.updateBestResults();
                        tgtDatabank.refreshGrid();
                        tgtDatabank.updateBestResults();
                    }
                    finally {
                        tgtProject.bestResults.enable();
                        srcProject.bestResults.enable();
                    }
                }
            }.start();
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot load strategies to PortfolioComposer.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Strategies moved.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void createPortfolio(Map<String, String[]> parameterMap) {
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            String strategies = this.tryGetParam(parameterMap, "strategies")[0];
            String[] stgs = strategies.split(",");
            String initialBalanceType = this.tryGetParam(parameterMap, "initialBalanceType")[0];
            Databank databank = this.getDatabank(parameterMap);
            if (stgs.length == 1 && stgs[0].equals("all")) {
                stgs = new String[databank.size()];
                databank.getRecordKeys().toArray(stgs);
            }
            project.publisher.resetLastData("progress-channel");
            ArrayList<ResultsGroup> results = new ArrayList<ResultsGroup>();
            try {
                for (String strategy : stgs) {
                    ResultsGroup rg = databank.getLocked(strategy, "onCreatePortfolio");
                    results.add(rg);
                }
                project.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Merging strategies", (Object[])new Object[0]));
                ResultsGroup portfolio = ResultsGroup.merge(results, (String[])new String[]{"AdditionalMarket", "CrossCheck_"}, (SQProject)project);
                project.getProgress().update("Create Portfolio", -1.0, null, L.t((String)"Creating portfolio result", (Object[])new Object[0]));
                portfolio.createPortfolioResult(initialBalanceType, project);
                Element strategyXml = portfolio.portfolio().getStrategyXml();
                if (strategyXml != null) {
                    strategyXml.setAttribute("mergedResult", "true");
                }
                databank.add(portfolio, true);
                databank.updateBestResults(portfolio);
                WebSocketNotification.sendSuccess((String)L.t((String)"Portfolio created '%s'", (Object[])new Object[]{portfolio.getName()}), (String[])new String[]{"SQUANT"});
            }
            finally {
                for (ResultsGroup rg : results) {
                    rg.releaseLock("onCreatePortfolio");
                }
                project.getProgress().update("Create Portfolio", 100.0, null);
            }
        }
        catch (Exception e) {
            Log.error("Creating portfolio failed.", (Throwable)e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String mergeStrategiesSync(Map<String, String[]> parameterMap) {
        SQProject project = null;
        try {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            project = ProjectEngine.get((String)projectName);
            if (project == null) {
                throw new Exception(L.t((String)"Project '%s' not found.", (Object[])new Object[]{projectName}));
            }
            String strategies = this.tryGetParam(parameterMap, "strategies")[0];
            String[] stgs = strategies.split(",");
            String portfolioName = this.tryGetParam(parameterMap, "name")[0];
            String destDatabankName = this.tryGetParam(parameterMap, "databank")[0];
            Databank destDatabank = (Databank)project.getDatabanks().get((Object)destDatabankName);
            if (destDatabank == null) {
                throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{destDatabankName}));
            }
            String mergeType = this.tryGetParam(parameterMap, "mergeType")[0];
            if (!(mergeType.equals("simulated") || mergeType.equals("merged") || mergeType.equals("signals"))) {
                throw new Exception(L.t((String)"Unknown merge type '%s', use one of: simulated, merged, signals.", (Object[])new Object[]{mergeType}));
            }
            String simulatedInitialCapital = parameterMap.containsKey("simulatedInitialCapital") ? this.tryGetParam(parameterMap, "simulatedInitialCapital")[0] : "first";
            int signalsConditionsPct = parameterMap.containsKey("signalsConditionsPct") ? Integer.parseInt(this.tryGetParam(parameterMap, "signalsConditionsPct")[0]) : 70;
            String signalsStrategy = parameterMap.containsKey("signalsStrategy") ? this.tryGetParam(parameterMap, "signalsStrategy")[0] : "";
            Databank databank = this.getDatabank(parameterMap);
            if (stgs.length == 1 && stgs[0].equals("all")) {
                stgs = new String[databank.size()];
                databank.getRecordKeys().toArray(stgs);
            }
            if (stgs.length < 2) {
                throw new Exception(L.t((String)"At least 2 strategies are required to merge, got %s.", (Object[])new Object[]{"" + stgs.length}));
            }
            if (mergeType.equals("signals") && signalsStrategy.isEmpty()) {
                throw new Exception(L.t((String)"Parameter '%s' is missing.", (Object[])new Object[]{"signalsStrategy"}));
            }
            project.publisher.resetLastData("progress-channel");
            ResultsGroup portfolio = null;
            ArrayList<ResultsGroup> results = new ArrayList<ResultsGroup>();
            try {
                for (String strategy : stgs) {
                    ResultsGroup rg = databank.getLocked(strategy, "onMergeStrategies");
                    results.add(rg);
                }
                project.getProgress().update("Merge strategies", -1.0, null, L.t((String)"Merging strategies", (Object[])new Object[0]));
                switch (mergeType) {
                    case "simulated": {
                        portfolio = StrategyMerger.createSimulatedResult((SQProject)project, results, (String)portfolioName, (String)simulatedInitialCapital);
                        break;
                    }
                    case "merged": {
                        portfolio = StrategyMerger.createMergedResult((SQProject)project, results, (String)portfolioName);
                        break;
                    }
                    case "signals": {
                        portfolio = StrategyMerger.createFuzzyResult((SQProject)project, results, (String)portfolioName, (int)signalsConditionsPct, (String)signalsStrategy);
                    }
                }
                destDatabank.add(portfolio, true);
                destDatabank.updateBestResults(portfolio);
                WebSocketNotification.sendSuccess((String)L.t((String)"Portfolio created '%s'", (Object[])new Object[]{portfolio.getName()}), (String[])new String[]{"SQUANT"});
            }
            finally {
                for (ResultsGroup rg : results) {
                    rg.releaseLock("onMergeStrategies");
                }
                project.getProgress().update("Merge strategies", 100.0, null);
            }
            JSONObject response = new JSONObject();
            response.put("success", (Object)L.t((String)"Portfolio created '%s'", (Object[])new Object[]{portfolio.getName()}));
            response.put("portfolio", (Object)portfolio.getName());
            response.put("databank", (Object)destDatabankName);
            return response.toString();
        }
        catch (Throwable e) {
            Log.error("Creating portfolio failed.", e);
            if (project != null) {
                project.getProgress().update("Merge strategies", 100.0, L.t((String)"Merging strategies failed", (Object[])new Object[0]) + " - " + e.getMessage(), null);
            }
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Merging strategies failed.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private String onGetDataItems(Map<String, String[]> parameterMap) {
        JSONObject response;
        block11: {
            response = new JSONObject();
            boolean isAlgoWizard = false;
            try {
                isAlgoWizard = Boolean.parseBoolean(this.tryGetParam(parameterMap, "algoWizard")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            ResultsGroup resultsGroup = null;
            String reportName = null;
            try {
                if (isAlgoWizard) {
                    resultsGroup = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{SQPaths.algoWizardStrategyPath});
                    DataItemsGenerator.get((JSONObject)response, (ResultsGroup)resultsGroup);
                    break block11;
                }
                reportName = this.tryGetParam(parameterMap, "reportName")[0];
                Databank databank = this.getDatabank(parameterMap);
                try {
                    resultsGroup = databank.getLocked(reportName, "onGetDataItems");
                    DataItemsGenerator.get((JSONObject)response, (ResultsGroup)resultsGroup);
                }
                catch (RecordNotFoundException e) {
                    JSONObject json = new JSONObject();
                    json.put("error", (Object)L.t((String)"Strategy '%s' doesn't exist.", (Object[])new Object[]{reportName}));
                    json.put("strDoesntExist", true);
                    String string = json.toString();
                    return string;
                }
                finally {
                    if (resultsGroup != null) {
                        resultsGroup.releaseLock("onGetDataItems");
                    }
                }
            }
            catch (Exception ex) {
                return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot get data items.", (Object[])new Object[0]), (Throwable)ex);
            }
        }
        response.put("success", (Object)L.t((String)"Data items listed.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSaveReports(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        SQProject project = null;
        try {
            String strategyName;
            int i;
            String folder = this.getParam(parameterMap, "folder", SQPaths.strategiesDirPath);
            String strategies = this.getParam(parameterMap, "strategies", "all");
            String fileName = this.getParam(parameterMap, "fileName", "not set");
            String extension = this.getParam(parameterMap, "extension[name]", "sqx");
            String prefix = this.getParam(parameterMap, "prefix", "");
            String sufix = this.getParam(parameterMap, "sufix", "");
            boolean handleMagicNumbers = Boolean.parseBoolean(this.getParam(parameterMap, "handleMagicNumbers", "false"));
            int startingNumber = Integer.parseInt(this.getParam(parameterMap, "startingNumber", "12345"));
            String[] stgs = strategies.split(",");
            Databank databank = this.getDatabank(parameterMap);
            project = ProjectEngine.get((String)databank.getProject());
            if (stgs.length == 1 && stgs[0].equals("all")) {
                stgs = new String[databank.size()];
                databank.getRecordKeys().toArray(stgs);
            }
            databank.getReportSaver().resetCounting();
            if (!MainApp.runInConsoleWithoutActiveWebserver()) {
                for (i = 0; i < stgs.length; ++i) {
                    strategyName = stgs[i];
                    String filePath = folder + "/" + (stgs.length > 1 || fileName.equals("not set") ? prefix + strategyName + sufix : fileName) + "." + extension;
                    try {
                        if (extension.equals("java")) {
                            filePath = folder + "/" + (stgs.length > 1 || fileName.equals("not set") ? SQUtils.correctClassName((String)(prefix + strategyName + sufix)) : SQUtils.correctClassName((String)fileName)) + "." + extension;
                        }
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    if (!new File(filePath).exists()) continue;
                    project.userConfirm.awaitConfirmation(L.t((String)"Overwrite confirm", (Object[])new Object[0]), L.t((String)"There already are strategies with the same name in the target folder. Do you want to overwrite them?", (Object[])new Object[0]));
                    if (project.userConfirm.isConfirmed()) break;
                    project.getProgress().update("save", 100.0, null);
                    response.put("success", (Object)L.t((String)"Canceled.", (Object[])new Object[0]));
                    return response.toString();
                }
            }
            new File(folder).mkdirs();
            for (i = 0; i < stgs.length; ++i) {
                strategyName = stgs[i];
                String targetFilePath = folder + "/" + (stgs.length > 1 || fileName.equals("not set") ? prefix + strategyName + sufix : fileName) + "." + extension;
                try {
                    if (extension.equals("java")) {
                        targetFilePath = folder + "/" + (stgs.length > 1 || fileName.equals("not set") ? SQUtils.correctClassName((String)(prefix + strategyName + sufix)) : SQUtils.correctClassName((String)fileName)) + "." + extension;
                    }
                }
                catch (Exception exception) {
                    // empty catch block
                }
                ResultsGroup rg = null;
                try {
                    rg = databank.getLocked(strategyName, "onSaveReports");
                    try {
                        databank.getReportSaver().save(rg, extension, targetFilePath, handleMagicNumbers, startingNumber, parameterMap);
                    }
                    catch (Exception e) {
                        Log.error("Error while saving strategy '" + strategyName + "'", (Throwable)e);
                        if (rg == null) continue;
                        rg.releaseLock("onSaveReports");
                        continue;
                    }
                }
                catch (Exception e) {
                    Log.warn("Strategy '" + strategyName + "' no longer exists (was probably replaced by a better strategy with the same fingerprint)");
                    continue;
                }
                finally {
                    if (rg != null) {
                        rg.releaseLock("onSaveReports");
                    }
                }
                project.getProgress().update("save", (double)i / (double)stgs.length * 100.0, null, L.t((String)"Saved %d / %d", (Object[])new Object[]{i, stgs.length}));
            }
            project.getProgress().update("save", 100.0, null);
        }
        catch (Exception e) {
            if (project != null) {
                project.getProgress().update("save", 100.0, null);
            }
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Saving reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Reports saved.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSaveSingleFileJava(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String folder = SQPaths.userDirPath;
            try {
                folder = this.tryGetParam(parameterMap, "folder")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            String filePath = this.tryGetParam(parameterMap, "filePath")[0];
            String[] extensions = null;
            String[] extensionDescriptions = null;
            try {
                JSONArray extensionsArray = this.tryGetJsonArray(parameterMap, "extension");
                if (extensionsArray.length() == 0) {
                    throw new Exception();
                }
                int count = extensionsArray.length();
                extensions = new String[count];
                extensionDescriptions = new String[count];
                for (int a = 0; a < count; ++a) {
                    JSONObject extensionObj = extensionsArray.getJSONObject(a);
                    extensions[a] = extensionObj.getString("name");
                    extensionDescriptions[a] = extensionObj.getString("description");
                }
            }
            catch (Exception e) {
                extensions = new String[]{this.tryGetParam(parameterMap, "extension[name]")[0]};
                extensionDescriptions = new String[]{this.tryGetParam(parameterMap, "extension[description]")[0]};
            }
            String fileName = this.tryGetParam(parameterMap, "fileName")[0];
            Databank databank = this.getDatabank(parameterMap);
            databank.getReportSaver().resetCounting();
            ResultsGroup rg = databank.getLocked(fileName, "onSaveSingleFileJava");
            int lastIndex = filePath.lastIndexOf(46);
            String ext = null;
            if (lastIndex == -1 || this.os.isUnix()) {
                if (extensions != null && extensions.length == 1) {
                    ext = extensions[0];
                    filePath = filePath + "." + ext;
                }
            } else {
                ext = SQUtils.getExtension((String)filePath);
            }
            try {
                File f = new File(filePath);
                databank.getReportSaver().save(rg, ext, filePath, false, 0, parameterMap);
                response.put("folder", (Object)f.getParent());
            }
            finally {
                rg.releaseLock("onSaveSingleFileJava");
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Saving reports failed.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"File saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetConfig(Map<String, String[]> args) {
        JsonCreator json = new JsonCreator();
        json.beginObject();
        try {
            String projectName = args.get("projectName")[0];
            json.putRaw("config", (Object)ProjectEngine.get((String)projectName).toJSON(), true);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot get project settings.", (Object[])new Object[0]), (Throwable)ex);
        }
        json.put("success", (Object)L.t((String)"XML config returned.", (Object[])new Object[0]), false);
        json.endObject(false);
        return json.toJson();
    }

    private String onCheckResources(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = args.get("projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            Element elResources = project.checkUnresolvedResources();
            if (elResources != null) {
                response.put("hasUnresolvedResources", true);
                response.put("resourcesXML", (Object)XMLUtil.xmlToStringRaw((Element)elResources));
            }
            response.put("config", (Object)project.toJSON());
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot get project settings.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"XML config returned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetTemplateConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String taskName = this.tryGetParam(args, "taskName")[0];
            String taskType = this.tryGetParam(args, "taskType")[0];
            String fileName = this.tryGetParam(args, "fileName")[0];
            String sampleName = null;
            try {
                sampleName = this.tryGetParam(args, "sampleName")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            boolean isSample = sampleName != null;
            File configFile = this.getTemplateFile(fileName, isSample);
            String fileContent = SQFileManager.loadFile((String)configFile.getAbsolutePath());
            Element xmlConfig = XMLUtil.stringToXmlElement((String)fileContent);
            if (xmlConfig.getName().equals("Blocks")) {
                response.put("xmlConfig", (Object)fileContent);
            } else {
                Element resourcesXML;
                Element templateConfig = this.prepareTaskConfig(xmlConfig, taskType);
                templateConfig.setAttribute("name", taskName);
                templateConfig.setAttribute("templateFile", fileName);
                if (isSample) {
                    templateConfig.setAttribute("sampleName", sampleName);
                }
                if ((resourcesXML = ProjectResources.checkTaskResources((Element)templateConfig)) != null) {
                    response.put("resourcesXML", (Object)XMLUtil.xmlToStringRaw((Element)resourcesXML));
                }
                response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)templateConfig));
            }
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot get task config settings.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"XML config returned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String fileContent;
            Element elTaskConfig;
            String fileName = this.tryGetParam(args, "file")[0];
            if (!fileName.endsWith(".cfx")) {
                fileName = fileName + ".cfx";
            }
            if ((elTaskConfig = XMLUtil.stringToXmlElement((String)(fileContent = SQFileManager.loadFile((String)fileName)))).getName() != "Task") {
                throw new Exception("Invalid task config, missing Task element.");
            }
            Element elSettings = elTaskConfig.getChild("Settings");
            if (elSettings == null) {
                throw new Exception("Invalid task config, missing Settings element.");
            }
            String projectName = this.tryGetParam(args, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            if (project.getTasksCount() == 0) {
                throw new Exception("The project is empty.");
            }
            ISQTask task = project.getTask(0);
            if (!XMLUtil.getAttr((Element)elTaskConfig, (String)"type", (String)"NA").equals(task.getType())) {
                throw new Exception("Cannot apply config of different type.");
            }
            String taskXMLFile = task.getTaskXMLFileName();
            Element elSettingsExisting = task.getConfig();
            elSettingsExisting.removeContent();
            for (Content content : elSettings.getContent()) {
                elSettingsExisting.addContent(content.clone());
            }
            SQFileManager.updateTaskConfig((File)project.getProjectConfigFile(), (String)taskXMLFile, (Element)elSettingsExisting);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)"Cannot load config. ", (Throwable)ex);
        }
        response.put("success", (Object)"Config loaded.");
        return response.toString();
    }

    private String onSaveConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName;
            SQProject project;
            String fileName = this.tryGetParam(args, "file")[0];
            if (!fileName.endsWith(".cfx")) {
                fileName = fileName + ".cfx";
            }
            if ((project = ProjectEngine.get((String)(projectName = this.tryGetParam(args, "projectName")[0]))).getTasksCount() == 0) {
                throw new Exception("The project is empty.");
            }
            ISQTask task = project.getTask(0);
            String taskXMLFile = null;
            try {
                taskXMLFile = this.tryGetParamValue(args, "taskXMLFile");
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (taskXMLFile != null && !taskXMLFile.isEmpty() && (task = project.getTaskByXMLFile(taskXMLFile)) == null) {
                throw new Exception(L.t((String)"Task '%s' not found in project '%s'.", (Object[])new Object[]{taskXMLFile, projectName}));
            }
            Element elTask = null;
            for (Element elTaskDef : project.getConfig().getChild("Tasks").getChildren("Task")) {
                if (!task.getTaskXMLFileName().equals(elTaskDef.getAttributeValue("taskXMLFile"))) continue;
                elTask = elTaskDef.clone();
                break;
            }
            if (elTask == null) {
                throw new Exception(L.t((String)"Task '%s' not found in project '%s'.", (Object[])new Object[]{task.getTaskXMLFileName(), projectName}));
            }
            Element elSettings = null;
            String xmlConfig = null;
            try {
                xmlConfig = this.tryGetParamValue(args, "xmlConfig");
            }
            catch (Exception exception) {
                // empty catch block
            }
            if (xmlConfig != null && !xmlConfig.isEmpty()) {
                elSettings = XMLUtil.stringToElement((String)xmlConfig);
                if (!elSettings.getName().equals("Settings")) {
                    throw new Exception("Invalid task config, missing Settings element.");
                }
            } else {
                elSettings = task.getConfig().clone();
            }
            ProjectResources.addResources((Element)elSettings);
            elTask.addContent((Content)elSettings);
            String fileContent = XMLUtil.elementToString((Element)elTask);
            SQFileManager.saveFile((String)fileName, (String)fileContent);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)"Cannot save config. ", (Throwable)ex);
        }
        response.put("success", (Object)"Config saved.");
        return response.toString();
    }

    private Element prepareTaskConfig(Element taskConfig, String taskType) throws Exception {
        String[] neededSettingsTemp = ProjectConfigHelper.getTaskSettings((String)taskType);
        String[] neededSettings = new String[neededSettingsTemp.length + 1];
        for (int i = 0; i < neededSettingsTemp.length; ++i) {
            neededSettings[i] = neededSettingsTemp[i];
        }
        neededSettings[neededSettings.length - 1] = "Resources";
        String defaultProjectName = null;
        if (!taskConfig.getName().equals("Task")) {
            throw new Exception(L.t((String)"Selected config is not a task template.", (Object[])new Object[0]));
        }
        Element newConfig = taskConfig.clone().detach();
        newConfig.setAttribute("type", taskType);
        newConfig.setAttribute("active", "true");
        Element newElSettings = XMLUtil.getChildElem((Element)newConfig, (String)"Settings");
        newElSettings.removeContent();
        switch (taskType) {
            case "Build": {
                defaultProjectName = "Builder";
                break;
            }
            case "Retest": {
                defaultProjectName = "Retester";
                break;
            }
            case "Optimize": {
                defaultProjectName = "Optimizer";
            }
        }
        Element elSettings = XMLUtil.getChildElem((Element)taskConfig, (String)"Settings");
        for (Element elSetting : elSettings.getChildren()) {
            String settingName = elSetting.getName();
            boolean settingWanted = false;
            for (int a = 0; a < neededSettings.length; ++a) {
                String setting = neededSettings[a];
                if (setting == null || !setting.equals(settingName)) continue;
                neededSettings[a] = null;
                settingWanted = true;
                break;
            }
            if (!settingWanted) continue;
            newElSettings.addContent((Content)elSetting.clone().detach());
        }
        if (defaultProjectName == null) {
            return newConfig;
        }
        DefaultProjectConfig defaultConfig = ProjectEngine.get((String)defaultProjectName).getDefaultConfig();
        Element defaultElSettings = defaultConfig.taskConfig;
        for (Element elSetting : defaultElSettings.getChildren()) {
            String settingName = elSetting.getName();
            if (settingName.equals("Databanks")) {
                newElSettings.addContent((Content)elSetting.clone().detach());
                continue;
            }
            for (int a = 0; a < neededSettings.length; ++a) {
                String setting = neededSettings[a];
                if (setting == null || !settingName.equals(setting)) continue;
                newElSettings.addContent((Content)elSetting.clone().detach());
            }
        }
        return newConfig;
    }

    private String onUpdateTemplateConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        String templateFile = null;
        try {
            String taskConfig = this.tryGetParam(args, "xmlConfig")[0];
            Element elTask = XMLUtil.stringToElement((String)taskConfig);
            if (!elTask.getName().equals("Task")) {
                throw new Exception(L.t((String)"Selected config is not a task config.", (Object[])new Object[0]));
            }
            templateFile = elTask.getAttributeValue("templateFile");
            File template = this.getTemplateFile(templateFile, false);
            Element elSettings = elTask.getChild("Settings");
            if (elSettings != null) {
                ProjectResources.addResources((Element)elSettings);
                taskConfig = XMLUtil.elementToString((Element)elTask);
            }
            SQFileManager.saveFile((String)template.getAbsolutePath(), (String)taskConfig, (Element)elTask);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot update template file '%s'.", (Object[])new Object[]{templateFile}), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Template config updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onApplySimpleTemplate(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String taskName = this.tryGetParam(args, "taskName")[0];
            String strategyType = this.tryGetParam(args, "strategyType")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            ISQTask task = project.getTaskByName(taskName);
            Element elSettingsCurrent = task.getConfig();
            File templateFile = new File(SQPaths.simpleTemplatesDirPath + "/" + strategyType + ".xml");
            if (!templateFile.exists()) {
                throw new Exception(L.t((String)"Template file '%s' not found.", (Object[])new Object[]{templateFile.getName()}));
            }
            Element elTask = XMLUtil.fileToXmlElement((File)templateFile);
            Element elSettingsNew = elTask.getChild("Settings");
            elSettingsCurrent.removeContent();
            for (Content content : elSettingsNew.getContent()) {
                elSettingsCurrent.addContent(content.clone());
            }
            SQFileManager.updateWholeProjectConfig((SQProject)project);
            response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
            response.put("taskXMLFile", (Object)task.getTaskXMLFileName());
            response.put("taskXML", (Object)XMLUtil.xmlToStringRaw((Element)elSettingsCurrent));
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot apply template config.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Template config applied.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetCurrentTemplateSettings(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String taskName = this.tryGetParam(args, "taskName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            Element elTaskCurrent = project.getTaskSettingsByName(taskName);
            String sampleName = elTaskCurrent.getAttributeValue("sampleName");
            if (sampleName != null && !sampleName.isEmpty()) {
                Element template = TaskConfigWorker.getTemplateSettings(sampleName);
                response.put("templateConfig", (Object)XMLUtil.xmlToStringRaw((Element)template));
            } else {
                Log.error("No template set in XML");
            }
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot apply template config.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Template config applied.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onResetTaskConfig(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.tryGetParam(args, "projectName")[0];
            String taskName = this.tryGetParam(args, "taskName")[0];
            String configName = this.tryGetParam(args, "configName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            ISQTask task = project.getTaskByName(taskName);
            Element defaultConfig = task.getDefaultConfig(configName).getChild("Settings");
            Element elSettingsCurrent = task.getConfig();
            elSettingsCurrent.removeContent();
            List settings = defaultConfig.getChildren();
            for (int a = 0; a < settings.size(); ++a) {
                elSettingsCurrent.addContent((Content)((Element)settings.get(a)).clone());
            }
            Element elTaskCurrent = ProjectConfigHelper.getTaskConfigByName((Element)project.getConfig(), (String)taskName);
            elTaskCurrent.setAttribute("sampleName", "Custom");
            elTaskCurrent.setAttribute("templateFile", "");
            SQFileManager.updateWholeProjectConfig((SQProject)project);
            response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
            response.put("taskXMLFile", (Object)task.getTaskXMLFileName());
            response.put("taskXML", (Object)XMLUtil.xmlToStringRaw((Element)elSettingsCurrent));
            response.put("simpleSettings", (Object)"Custom");
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot apply template config.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Template config applied.", (Object[])new Object[0]));
        return response.toString();
    }

    private File getTemplateFile(String fileName, boolean isSample) throws Exception {
        String filePath;
        File configFile = new File(fileName);
        if (!configFile.exists()) {
            if (!fileName.endsWith(".cfx")) {
                fileName = fileName + ".cfx";
            }
            configFile = new File(fileName);
        }
        if (!configFile.exists() && !(configFile = new File(filePath = (isSample ? SQPaths.buildTemplatesDirPath : SQPaths.configsDirPath) + "/" + fileName)).exists()) {
            throw new Exception(String.format("Config file '%s' not found", filePath));
        }
        return configFile;
    }

    private synchronized String onUpdateTaskXML(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        String projectName = null;
        String taskXMLFile = null;
        try {
            projectName = this.tryGetParam(args, "projectName")[0];
            taskXMLFile = this.tryGetParam(args, "taskXMLFile")[0];
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            Element elSettings = XMLUtil.stringToElement((String)xmlConfig);
            SQProject project = ProjectEngine.get((String)projectName);
            project.checkProjectStatus("update");
            ISQTask task = project.getTaskByXMLFile(taskXMLFile);
            boolean updateWholeProject = false;
            if (task.getType().equals("Build")) {
                String newSampleName;
                Element elTaskDef = ProjectConfigHelper.getTaskConfigByXMLFile((Element)project.getConfig(), (String)taskXMLFile);
                String sampleName = elTaskDef.getAttributeValue("sampleName");
                boolean isCustom = TaskConfigWorker.isCustomSettings(sampleName, elSettings);
                JSONObject simpleSettings = new JSONObject();
                simpleSettings.put("strategyType", (Object)(isCustom ? "Custom" : sampleName));
                response.put("simpleSettings", (Object)simpleSettings);
                String string = newSampleName = isCustom ? "Custom" : sampleName;
                if (newSampleName != null && !newSampleName.equals(sampleName)) {
                    elTaskDef.setAttribute("sampleName", newSampleName);
                    updateWholeProject = true;
                }
            }
            Element taskConfig = task.getConfig();
            taskConfig.removeContent();
            for (Content content : elSettings.getContent()) {
                taskConfig.addContent(content.clone());
            }
            if (updateWholeProject) {
                SQFileManager.updateWholeProjectConfig((SQProject)project);
            } else {
                ProjectResources.addResources((ISQTask)task);
                SQFileManager.updateTaskConfig((File)project.getProjectConfigFile(), (String)taskXMLFile, (Element)task.getConfig());
            }
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot update settings of task file '%s', project '%s'.", (Object[])new Object[]{taskXMLFile, projectName}), (Throwable)ex);
        }
        String[] notifyUI = args.get("notifyUI");
        if (notifyUI != null && notifyUI.length > 0 && "true".equals(notifyUI[0])) {
            SQWebSocketManager.addToDataQueue((DataToSend)new DataToSend("taskConfigChanged", new JSONObject().put("projectName", (Object)projectName).put("taskXMLFile", (Object)taskXMLFile)), (String[])new String[]{SQWebSocketManager.getProductCode((String)projectName), "TASKMANAGER"});
        }
        response.put("success", (Object)L.t((String)"Task XML config updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private synchronized String onUpdateProjectXML(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        String projectName = null;
        try {
            projectName = this.tryGetParam(args, "projectName")[0];
            String xmlConfig = this.tryGetParam(args, "xmlConfig")[0];
            Element config = XMLUtil.stringToElement((String)xmlConfig);
            SQProject project = ProjectEngine.get((String)projectName);
            project.updateConfig(config);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot update settings of project '%s'.", (Object[])new Object[]{projectName}), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Project XML config updated.", (Object[])new Object[0]));
        return response.toString();
    }

    private Databank getDatabank(Map<String, String[]> args) throws Exception {
        String projectName = this.tryGetParam(args, "projectName")[0];
        String databankName = this.tryGetParam(args, "databankName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        if (!project.getDatabanks().containsKey((Object)databankName)) {
            throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{databankName}));
        }
        return (Databank)project.getDatabanks().get((Object)databankName);
    }

    private String onRetest(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String strategies = args.get("strategies")[0];
            String srcProjectName = args.get("srcProjectName")[0];
            String srcDatabankName = args.get("srcDatabankName")[0];
            final boolean move = Boolean.parseBoolean(args.get("move")[0]);
            MainApp.settings().set("retestMove", move + "");
            boolean allStrategies = false;
            String srcTaskName = null;
            try {
                srcTaskName = args.get("srcTaskName")[0];
            }
            catch (Exception exception) {
                // empty catch block
            }
            final SQProject retesterProject = ProjectEngine.get((String)"Retester");
            final Databank retesterDatabank = (Databank)retesterProject.getDatabanks().get((Object)"Results");
            final SQProject srcProject = ProjectEngine.get((String)srcProjectName);
            final Databank srcDatabank = (Databank)srcProject.getDatabanks().get((Object)srcDatabankName);
            final String[] strategiesArray = strategies.split(",");
            if (strategiesArray.length == 1 && strategiesArray[0].equals("all")) {
                allStrategies = true;
            }
            if (srcTaskName != null) {
                try {
                    Element elSettings = ProjectEngine.get((String)srcProjectName).getTaskSettingsByName(srcTaskName);
                    if (elSettings == null) {
                        throw new Exception(L.t((String)"Task settings not found.", (Object[])new Object[0]));
                    }
                    response.put("newConfig", (Object)XMLUtil.xmlToStringRaw((Element)elSettings));
                }
                catch (Exception e) {
                    throw new Exception(L.t((String)"Cannot get config of task '%s'.", (Object[])new Object[]{srcTaskName}));
                }
            }
            final boolean takeAllStrategies = allStrategies;
            new Thread(this){
                final /* synthetic */ ProjectServlet this$0;
                {
                    this.this$0 = this$0;
                }

                /*
                 * WARNING - Removed try catching itself - possible behaviour change.
                 */
                @Override
                public void run() {
                    try {
                        Exception lastException = null;
                        retesterProject.bestResults.disable();
                        srcProject.bestResults.disable();
                        retesterProject.publisher.resetLastData("progress-channel");
                        if (takeAllStrategies) {
                            ArrayList records = srcDatabank.getRecordKeys();
                            int count = records.size();
                            for (int i = 0; i < records.size(); ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked((String)records.get(i), "onRetest");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onRetest");
                                    }
                                    if (move) {
                                        srcDatabank.remove(rgCloned.getName(), true, true, false, false, "onRetest");
                                    }
                                    retesterDatabank.add(rgCloned, false);
                                    retesterProject.getProgress().update("retest", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to retester failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        } else {
                            int count = strategiesArray.length;
                            for (int i = 0; i < strategiesArray.length; ++i) {
                                try {
                                    double percent = (double)i / (double)count * 100.0;
                                    ResultsGroup rg = srcDatabank.getLocked(strategiesArray[i], "onRetest");
                                    ResultsGroup rgCloned = null;
                                    try {
                                        rgCloned = rg.clone();
                                    }
                                    finally {
                                        rg.releaseLock("onRetest");
                                    }
                                    if (move) {
                                        srcDatabank.remove(rgCloned.getName(), true, true, false, false, "onRetest");
                                    }
                                    retesterDatabank.add(rgCloned, false);
                                    retesterProject.getProgress().update("retest", percent, null);
                                    continue;
                                }
                                catch (Exception e) {
                                    Log.error("Moving strategy to retester failed", (Throwable)e);
                                    lastException = e;
                                }
                            }
                        }
                        srcDatabank.refreshGrid();
                        retesterDatabank.refreshGrid();
                        retesterProject.getProgress().update("retest", 100.0, lastException == null ? null : "Some strategies were not loaded because of errors.");
                        srcDatabank.updateBestResults();
                        retesterDatabank.updateBestResults();
                    }
                    catch (Exception e) {
                        Log.error("Moving strategies to retester failed", (Throwable)e);
                        retesterProject.getProgress().update("retest", 100.0, "Moving strategies failed. " + e.getMessage());
                    }
                    catch (OutOfMemoryError e) {
                        retesterProject.getProgress().update("retest", 100.0, e.getMessage());
                        srcDatabank.refreshGrid();
                        srcDatabank.updateBestResults();
                        retesterDatabank.refreshGrid();
                        retesterDatabank.updateBestResults();
                    }
                    finally {
                        retesterProject.bestResults.enable();
                        srcProject.bestResults.enable();
                    }
                }
            }.start();
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot load strategies to retest.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Strategies loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onConfirm(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = args.get("projectName")[0];
            boolean confirmed = Boolean.parseBoolean(args.get("confirmed")[0]);
            ProjectEngine.get((String)projectName).confirm(confirmed);
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Confirmation failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Action confirmed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadGridData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        boolean refreshAction = false;
        try {
            refreshAction = Boolean.parseBoolean(args.get("refreshAction")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            String projectName = args.get("projectName")[0];
            String databankName = args.get("databankName")[0];
            if (refreshAction) {
                Log.info("Refresh called on databank " + projectName + "/" + databankName + "...");
            }
            boolean first1000 = false;
            try {
                first1000 = Boolean.parseBoolean(args.get("first1000")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            long lastChangeTime = Long.parseLong(args.get("lastChangeTime")[0]);
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            if (databank == null) {
                throw new Exception(L.t((String)"Databank '%s' doesn't exist.", (Object[])new Object[]{databankName}));
            }
            if (refreshAction) {
                Log.info("Total strategies in databank: " + databank.size());
            }
            JSONArray gridData = new JSONArray();
            response.put("loadTime", System.currentTimeMillis());
            if (databank.getLastChangeTime() > lastChangeTime) {
                ArrayList bufferData = databank.getBufferData(first1000);
                for (int i = 0; i < bufferData.size(); ++i) {
                    Object[] data = (Object[])bufferData.get(i);
                    JSONArray rowData = new JSONArray();
                    for (Object value : data) {
                        rowData.put(value);
                    }
                    gridData.put((Object)rowData);
                }
                response.put("gridData", (Object)gridData);
            } else {
                response.put("nothingChanged", true);
            }
            response.put("totalCount", databank.size());
        }
        catch (Exception ex) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Loading strategies failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        if (refreshAction) {
            Log.info("Sending strategies to frontend...");
        }
        response.put("success", (Object)L.t((String)"Strategies loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onSetDatabankColumnValue(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String value = args.get("value")[0];
            String columnName = args.get("column")[0];
            String strategyName = args.get("strategyName")[0];
            Databank databank = this.getDatabank(args);
            ResultsGroup rg = databank.getLocked(strategyName, "onSetDatabankColumnValue");
            try {
                DatabankColumn column = (DatabankColumn)DatabankColumns.get().findClassByName(columnName);
                column.setValue((Object)rg, (Object)value);
            }
            finally {
                if (rg != null) {
                    rg.releaseLock("onSetDatabankColumnValue");
                }
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot change databank column value.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Databank column value changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSetDatabankSynchronization(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String type = this.tryGetParam(args, "syncType")[0];
            Databank databank = this.getDatabank(args);
            databank.setSyncType(type);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot change synchronization settings.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Synchronization settings changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSyncfromfiles(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            final Databank databank = this.getDatabank(args);
            databank.loadStrategies(new IProgressListener(){
                final /* synthetic */ ProjectServlet this$0;
                {
                    this.this$0 = this$0;
                }

                public void onError(double percent, String error) {
                    CLILogger.log((String)L.t((String)"Loading strategies to databank '%s' failed - %s", (Object[])new Object[]{databank.getName(), error}));
                }

                public void onDone() {
                    CLILogger.log((String)L.t((String)"Loaded %d strategies to databank %s", (Object[])new Object[]{databank.size(), databank.getName()}));
                }

                public void onProgress(double percentDone) {
                }
            });
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot synchronize databank.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onSynchronizeDatabank(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            Databank databank = this.getDatabank(args);
            databank.synchronizeNow(String.format("API request project/synchronizeDatabank %s/%s.", databank.getProject(), databank.getName()));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot synchronize databank.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Synchronization started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onPrintToLog(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String message = this.tryGetParam(args, "message")[0];
            boolean isError = Boolean.parseBoolean(args.get("isError")[0]);
            if (isError) {
                Log.error("UI error: " + message);
            } else {
                Log.info("UI message: " + message);
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot log message.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Message logged.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCutStrategies(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            SQProject project;
            Databank databank = this.getDatabank(args);
            String[] strategies = this.getParam(args, "strategies", "all").split(",");
            if (strategies[0].equals("all")) {
                ArrayList records = databank.getRecordKeys();
                strategies = records.toArray(new String[records.size()]);
            }
            if (!(project = ProjectEngine.get((String)databank.getProject())).getName().equals("Builder") && project.isRunning()) {
                throw new Exception(L.t((String)"Project is running.", (Object[])new Object[0]));
            }
            StrategiesActionCache.cutFrom((Databank)databank, (String[])strategies);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot cut strategies.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Strategies cut.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCopyStrategies(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            Databank databank = this.getDatabank(args);
            String[] strategies = this.getParam(args, "strategies", "all").split(",");
            if (strategies[0].equals("all")) {
                ArrayList records = databank.getRecordKeys();
                strategies = records.toArray(new String[records.size()]);
            }
            StrategiesActionCache.copyFrom((Databank)databank, (String[])strategies);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot copy strategies.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Strategies copied.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onPasteStrategies(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            Databank databank = this.getDatabank(args);
            SQProject project = ProjectEngine.get((String)databank.getProject());
            if (!project.getName().equals("Builder") && project.isRunning()) {
                throw new Exception(L.t((String)"Project is running.", (Object[])new Object[0]));
            }
            StrategiesActionCache.pasteTo((Databank)databank);
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot paste strategies.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Strategies pasted.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onResolveResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"configXML", "resourcesXML", "actionType"});
        JSONObject response = new JSONObject();
        String configXML = this.tryGetParamValue(args, "configXML");
        String resourcesXML = this.tryGetParamValue(args, "resourcesXML");
        String filePath = null;
        try {
            filePath = this.tryGetParamValue(args, "filePath");
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            Element elConfig = XMLUtil.stringToElement((String)configXML);
            Element elResources = XMLUtil.stringToElement((String)resourcesXML);
            JSONArray newSymbols = new JSONArray();
            HashMap tasks = null;
            if (filePath != null) {
                tasks = SQProject.projectIsOlderThan136((Element)elConfig) ? SQFileManager.convertOldProjectConfig((Element)elConfig) : SQFileManager.loadTaskConfigs((File)new File(filePath));
            }
            boolean continueLoading = ProjectResources.resolveResources((Element)elResources, (Element)elConfig, (HashMap)tasks, (JSONArray)newSymbols, null);
            if (tasks != null) {
                JSONObject taskConfigs = new JSONObject();
                for (String taskXMLFile : tasks.keySet()) {
                    Element taskConfig = (Element)tasks.get(taskXMLFile);
                    if (continueLoading) {
                        ProjectResources.addResources((Element)taskConfig);
                    }
                    taskConfigs.put(taskXMLFile, (Object)XMLUtil.elementToString((Element)taskConfig));
                }
                response.put("taskConfigs", (Object)taskConfigs);
            }
            response.put("continueLoading", continueLoading);
            response.put("newSymbols", (Object)newSymbols);
            response.put("configXML", (Object)XMLUtil.elementToString((Element)elConfig));
            response.put("success", (Object)L.t((String)"Resources resolved.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resolve resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onCancelResolving() {
        JSONObject response = new JSONObject();
        ProjectResources.cancelImport();
        response.put("success", (Object)L.t((String)"Project import canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCheckCustomResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"configXML", "actionType"});
        JSONObject response = new JSONObject();
        String configXML = this.tryGetParamValue(args, "configXML");
        ArrayList<Element> taskConfigs = new ArrayList<Element>();
        try {
            JSONObject taskConfigsObj = this.tryGetJsonObject(args, "taskConfigs");
            Iterator it = taskConfigsObj.keys();
            while (it.hasNext()) {
                String key = (String)it.next();
                taskConfigs.add(XMLUtil.stringToElement((String)taskConfigsObj.getString(key)));
            }
        }
        catch (Exception taskConfigsObj) {
            // empty catch block
        }
        int actionType = Integer.parseInt(this.tryGetParamValue(args, "actionType"));
        try {
            Element config = XMLUtil.stringToElement((String)configXML);
            Element elResources = null;
            if (actionType == 3 || actionType == 4) {
                Element elStrategy = config.getChild("Strategy");
                elResources = ProjectCustomResources.checkStrategyResources((Element)elStrategy);
            } else {
                taskConfigs.add(config);
                elResources = ProjectCustomResources.checkProjectResources(taskConfigs);
            }
            response.put("success", (Object)L.t((String)"Custom resources checked.", (Object[])new Object[0]));
            response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)elResources));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resolve custom resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onCheckTemplateResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"filePath"});
        JSONObject response = new JSONObject();
        String filePath = this.tryGetParamValue(args, "filePath");
        try {
            IProgram loader = Program.get((String)"Loader");
            filePath = filePath.replace("\\", "/");
            filePath = filePath.contains("/") ? filePath : SQPaths.strategyTemplatesDirPath + "/" + filePath;
            ResultsGroup rg = (ResultsGroup)loader.call("loadFile", new Object[]{filePath});
            Element config = rg.getStrategyXml();
            Element elStrategy = config.getChild("Strategy");
            Element elResources = ProjectCustomResources.checkStrategyResources((Element)elStrategy);
            response.put("success", (Object)L.t((String)"Custom resources checked.", (Object[])new Object[0]));
            response.put("configXML", (Object)XMLUtil.elementToString((Element)config));
            response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)elResources));
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resolve custom resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onResolveCustomResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"configXML", "resourcesXML", "actionType"});
        JSONObject response = new JSONObject();
        String configXML = this.tryGetParamValue(args, "configXML");
        String resourcesXML = this.tryGetParamValue(args, "resourcesXML");
        int actionType = Integer.parseInt(this.tryGetParamValue(args, "actionType"));
        String filePath = null;
        try {
            filePath = this.tryGetParamValue(args, "filePath");
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            Element elResources = XMLUtil.stringToElement((String)resourcesXML);
            Element elConfig = ProjectCustomResources.resolveStrategyResources((Element)elResources, (Element)XMLUtil.stringToElement((String)configXML));
            switch (actionType) {
                case 0: {
                    HashMap taskConfigs = new HashMap();
                    try {
                        if (SQProject.projectIsOlderThan136((Element)elConfig)) {
                            taskConfigs = SQFileManager.convertOldProjectConfig((Element)elConfig);
                        } else {
                            JSONObject taskConfigsObj = this.tryGetJsonObject(args, "taskConfigs");
                            Iterator it = taskConfigsObj.keys();
                            while (it.hasNext()) {
                                String taskXMLFile = (String)it.next();
                                taskConfigs.put(taskXMLFile, XMLUtil.stringToElement((String)taskConfigsObj.getString(taskXMLFile)));
                            }
                        }
                    }
                    catch (Exception e) {
                        Log.error("Error while preparing task configs", (Throwable)e);
                        return ProjectServlet.apiErrorJSON((String)L.t((String)"Error while preparing task configs.", (Object[])new Object[0]), (Throwable)e);
                    }
                    elConfig.setAttribute("version", MainApp.getAppVersion());
                    String projectName = elConfig.getAttributeValue("name");
                    if (projectName == null) {
                        return ProjectServlet.apiErrorJSON((String)L.t((String)"Corrupted Project config file. Missing project name.", (Object[])new Object[0]), null);
                    }
                    if (filePath == null) {
                        return ProjectServlet.apiErrorJSON((String)L.t((String)"Project file path not specified.", (Object[])new Object[0]), null);
                    }
                    SQProject project = ProjectEngine.add((String)projectName, (File)new File(filePath), (Element)elConfig, (HashMap)taskConfigs);
                    response.put("loaded", true);
                    response.put("projectXML", (Object)XMLUtil.elementToString((Element)elConfig));
                    response.put("success", (Object)String.format("Project loaded '%s'.", project.getName()));
                    break;
                }
                case 1: 
                case 2: {
                    response.put("taskXML", (Object)XMLUtil.elementToString((Element)elConfig));
                    response.put("success", (Object)L.t((String)"Custom resources resolved.", (Object[])new Object[0]));
                    break;
                }
                case 3: {
                    try (ZipOutputStream target = null;){
                        Manifest manifest = new Manifest();
                        manifest.getMainAttributes().put(Attributes.Name.MANIFEST_VERSION, "1.0");
                        target = new JarOutputStream((OutputStream)new BufferedOutputStream(new FileOutputStream(filePath)), manifest);
                        JarEntry entry = new JarEntry("strategy_Portfolio.xml");
                        ((JarOutputStream)target).putNextEntry(entry);
                        Document myDocument = new Document(elConfig.clone());
                        BufferedWriter outputStream = new BufferedWriter(new OutputStreamWriter((OutputStream)target, "UTF8"));
                        XMLOutputter outputter = new XMLOutputter(Format.getPrettyFormat());
                        outputter.output(myDocument, (Writer)outputStream);
                        response.put("success", (Object)L.t((String)"Custom resources resolved.", (Object[])new Object[0]));
                        break;
                    }
                }
                case 4: {
                    response.put("success", (Object)L.t((String)"Custom resources resolved.", (Object[])new Object[0]));
                    break;
                }
                case 5: {
                    HashMap<String, Element> taskConfigs = new HashMap<String, Element>();
                    try {
                        JSONObject taskConfigsObj = this.tryGetJsonObject(args, "taskConfigs");
                        Iterator it = taskConfigsObj.keys();
                        while (it.hasNext()) {
                            String taskXMLFile = (String)it.next();
                            taskConfigs.put(taskXMLFile, XMLUtil.stringToElement((String)taskConfigsObj.getString(taskXMLFile)));
                        }
                    }
                    catch (Exception e) {
                        Log.error("Error while preparing task configs", (Throwable)e);
                        return ProjectServlet.apiErrorJSON((String)L.t((String)"Error while preparing task configs.", (Object[])new Object[0]), (Throwable)e);
                    }
                    String projectName = elConfig.getAttributeValue("name");
                    if (projectName == null) {
                        return ProjectServlet.apiErrorJSON((String)L.t((String)"Missing project name.", (Object[])new Object[0]), null);
                    }
                    SQProject project = ProjectEngine.get((String)projectName);
                    SQFileManager.updateTaskConfigurations((SQProject)project, taskConfigs);
                    response.put("projectXML", (Object)XMLUtil.elementToString((Element)elConfig));
                    project.setUnresolvedResources(false);
                    response.put("success", (Object)L.t((String)"Project resources resolved.", (Object[])new Object[0]));
                    break;
                }
                default: {
                    return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resolve resources - unknown action type %s.", (Object[])new Object[]{actionType}), null);
                }
            }
        }
        catch (Exception e) {
            return ProjectServlet.apiErrorJSON((String)L.t((String)"Cannot resolve custom resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onStatus(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            String projectName = this.tryGetParam(parameterMap, "projectName")[0];
            SQProject project = ProjectEngine.get((String)projectName);
            JSONObject engineObj = project.getInfo();
            ProjectRunInfo runInfo = project.getTrackingInfo();
            String strategiesAcceptedPct = SQUtils.d2((double)(100.0 * runInfo.strategiesAcceptedPct));
            String strategiesRejectedPct = SQUtils.d2((double)(100.0 * runInfo.strategiesRejectedPct));
            if (runInfo.strategiesAccepted > 0L && strategiesAcceptedPct.equals("0.00")) {
                strategiesAcceptedPct = "0.01";
                strategiesRejectedPct = "99.99";
            }
            if (projectName.equals("Builder")) {
                CLILogger.log((String)L.t((String)"Strategies generated", (Object[])new Object[0]), (String)(runInfo.totalJobsDone + ""), (int)50);
                CLILogger.log((String)L.t((String)"Time per strategy", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timePerStrategy), (int)50);
                CLILogger.log((String)L.t((String)"Time per accepted strategy", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timePerAcceptedStrategy), (int)50);
                CLILogger.log((String)L.t((String)"Rejected", (Object[])new Object[0]), (String)(strategiesRejectedPct + " %"), (int)50);
                CLILogger.log((String)L.t((String)"Accepted", (Object[])new Object[0]), (String)(strategiesAcceptedPct + " %"), (int)50);
                CLILogger.log((String)L.t((String)"Strategies per hour", (Object[])new Object[0]), (String)this.formatIntOrDouble(runInfo.strategiesPerHour), (int)50);
                CLILogger.log((String)L.t((String)"Accepted strategies per hour", (Object[])new Object[0]), (String)this.formatIntOrDouble(runInfo.acceptedStrategiesPerHour), (int)50);
                CLILogger.log((String)L.t((String)"Running time so far", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.taskRunningTime), (int)50);
                CLILogger.log((String)L.t((String)"In databank", (Object[])new Object[0]), (String)(engineObj.getInt("strategies") + ""), (int)50);
            } else if (projectName.equals("Retester")) {
                CLILogger.log((String)L.t((String)"Total tested", (Object[])new Object[0]), (String)(runInfo.totalJobsDone + ""), (int)50);
                CLILogger.log((String)L.t((String)"Time per strategy", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timePerStrategy), (int)50);
                CLILogger.log((String)L.t((String)"Strategies per hour", (Object[])new Object[0]), (String)this.formatIntOrDouble(runInfo.strategiesPerHour), (int)50);
                CLILogger.log((String)L.t((String)"In databank", (Object[])new Object[0]), (String)(engineObj.getInt("strategies") + ""), (int)50);
                CLILogger.log((String)L.t((String)"Failed", (Object[])new Object[0]), (String)(runInfo.strategiesFailed + ""), (int)50);
                CLILogger.log((String)L.t((String)"Passed", (Object[])new Object[0]), (String)(runInfo.strategiesPassed + ""), (int)50);
                CLILogger.log((String)L.t((String)"Running time so far", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.totalProjectRunningTime), (int)50);
                CLILogger.log((String)L.t((String)"Estimated time to finish", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timeToFinish), (int)50);
            } else if (projectName.equals("Optimizer")) {
                CLILogger.log((String)L.t((String)"Total steps", (Object[])new Object[0]), (String)(runInfo.totalSteps + ""), (int)50);
                CLILogger.log((String)L.t((String)"Step", (Object[])new Object[0]), (String)(runInfo.step + ""), (int)50);
                CLILogger.log((String)L.t((String)"Running time so far", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.taskRunningTime), (int)50);
                CLILogger.log((String)L.t((String)"Estimated time to finish", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timeToFinish), (int)50);
            } else {
                CLILogger.log((String)L.t((String)"Strategies generated", (Object[])new Object[0]), (String)(runInfo.totalJobsDone + ""), (int)50);
                CLILogger.log((String)L.t((String)"Time per strategy", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timePerStrategy), (int)50);
                CLILogger.log((String)L.t((String)"Time per accepted strategy", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.timePerAcceptedStrategy), (int)50);
                CLILogger.log((String)L.t((String)"Rejected", (Object[])new Object[0]), (String)(strategiesRejectedPct + " %"), (int)50);
                CLILogger.log((String)L.t((String)"Accepted", (Object[])new Object[0]), (String)(strategiesAcceptedPct + " %"), (int)50);
                CLILogger.log((String)L.t((String)"Failed", (Object[])new Object[0]), (String)(runInfo.strategiesFailed + ""), (int)50);
                CLILogger.log((String)L.t((String)"Passed", (Object[])new Object[0]), (String)(runInfo.strategiesPassed + ""), (int)50);
                CLILogger.log((String)L.t((String)"Strategies per hour", (Object[])new Object[0]), (String)this.formatIntOrDouble(runInfo.strategiesPerHour), (int)50);
                CLILogger.log((String)L.t((String)"Accepted strategies per hour", (Object[])new Object[0]), (String)this.formatIntOrDouble(runInfo.acceptedStrategiesPerHour), (int)50);
                CLILogger.log((String)L.t((String)"Running time so far", (Object[])new Object[0]), (String)SQUtils.formatDuration((long)runInfo.totalProjectRunningTime), (int)50);
                CLILogger.log((String)L.t((String)"In databank", (Object[])new Object[0]), (String)(engineObj.getInt("strategies") + ""), (int)50);
            }
        } else {
            throw new Exception(L.t((String)"Not implemented.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onList() throws Exception {
        JSONObject response = new JSONObject();
        List list = ProjectEngine.list();
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            for (int i = 0; i < list.size(); ++i) {
                CLILogger.log((String)((SQProject)list.get(i)).getName());
            }
        } else {
            JSONArray projects = new JSONArray();
            for (SQProject project : list) {
                JSONObject p = new JSONObject();
                p.put("name", (Object)project.getName());
                projects.put((Object)p);
            }
            response.put("projects", (Object)projects);
            response.put("success", (Object)L.t((String)"Projects listed.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String formatIntOrDouble(double value) {
        if (value > 1000.0) {
            return String.format("%.0f", value);
        }
        return String.format("%.2f", value);
    }

    private String onMergeWFStrategies(final Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        new Thread(this){
            final /* synthetic */ ProjectServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0.mergeWFStrategies(parameterMap);
            }
        }.start();
        response.put("success", (Object)L.t((String)"Merging WF strategies started.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void mergeWFStrategies(Map<String, String[]> parameterMap) {
        block8: {
            SQProject project = null;
            try {
                String projectName = this.tryGetParam(parameterMap, "projectName")[0];
                project = ProjectEngine.get((String)projectName);
                String strategies = this.tryGetParam(parameterMap, "strategies")[0];
                String[] stgs = strategies.split(",");
                String portfolioName = "Portfolio";
                String destDatabankName = this.tryGetParam(parameterMap, "databankName")[0];
                Databank destDatabank = (Databank)project.getDatabanks().get((Object)destDatabankName);
                Databank databank = this.getDatabank(parameterMap);
                if (stgs.length == 1 && stgs[0].equals("all")) {
                    stgs = new String[databank.size()];
                    databank.getRecordKeys().toArray(stgs);
                }
                project.publisher.resetLastData("progress-channel");
                ArrayList<ResultsGroup> results = new ArrayList<ResultsGroup>();
                try {
                    for (String strategy : stgs) {
                        ResultsGroup rg = databank.getLocked(strategy, "onMergeStrategies");
                        results.add(rg);
                    }
                    project.getProgress().update("Merge strategies", -1.0, null, L.t((String)"Merging WF strategies", (Object[])new Object[0]));
                    ResultsGroup portfolio = StrategyMerger.createSimulatedWFResult((SQProject)project, results, (String)portfolioName);
                    destDatabank.add(portfolio, true);
                    destDatabank.updateBestResults(portfolio);
                    WebSocketNotification.sendSuccess((String)L.t((String)"Portfolio created '%s'", (Object[])new Object[]{portfolio.getName()}), (String[])new String[]{"SQUANT"});
                }
                finally {
                    for (ResultsGroup rg : results) {
                        rg.releaseLock("onMergeStrategies");
                    }
                    project.getProgress().update("Merge strategies", 100.0, null);
                }
            }
            catch (Throwable e) {
                Log.error("Creating portfolio failed.", e);
                if (project == null) break block8;
                project.getProgress().update("Merge strategies", 100.0, L.t((String)"Merging strategies failed", (Object[])new Object[0]) + " - " + e.getMessage(), null);
            }
        }
    }
}

