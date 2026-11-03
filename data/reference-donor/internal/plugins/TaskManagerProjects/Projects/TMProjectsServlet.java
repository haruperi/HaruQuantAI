/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.file.SQFileManager
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectFileValidator
 *  com.strategyquant.tradinglib.project.ProjectNameComparator
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.taskImpl.ISQTask
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.TaskManager.impl.Projects;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.file.SQFileManager;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectFileValidator;
import com.strategyquant.tradinglib.project.ProjectNameComparator;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Pattern;
import org.jdom2.Content;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TMProjectsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(TMProjectsServlet.class);
    private static final Pattern FORBIDDEN_PROJECT_NAME_CHARS = Pattern.compile("[\\\\/:*?\"<>|]");
    private static final Pattern RESERVED_PROJECT_NAME = Pattern.compile("^(nul|prn|con|lpt[0-9]|com[0-9])(\\.|$).*", 2);
    private ProjectNameComparator projectNameComparator = new ProjectNameComparator();

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "listProjects": {
                return this.onListProjects();
            }
            case "createProject": {
                return this.onCreateProject(parameterMap);
            }
            case "openProject": {
                return this.onOpenProject(parameterMap);
            }
            case "validateProject": {
                return this.onValidateProject(parameterMap);
            }
            case "saveProject": {
                return this.onSaveProject(parameterMap);
            }
            case "removeProject": {
                return this.onRemoveProject(parameterMap);
            }
            case "cloneProject": {
                return this.onCloneProject(parameterMap);
            }
            case "renameProject": {
                return this.onRenameProject(parameterMap);
            }
            case "addTask": {
                return this.onAddTask(parameterMap);
            }
            case "removeTask": {
                return this.onRemoveTask(parameterMap);
            }
            case "getAvailableTasks": {
                return this.onGetAvailableTasks();
            }
            case "moveTask": {
                return this.onMoveTask(parameterMap);
            }
            case "renameTask": {
                return this.onRenameTask(parameterMap);
            }
            case "cloneTask": {
                return this.onCloneTask(parameterMap);
            }
            case "activateTask": {
                return this.onActivateTask(parameterMap);
            }
            case "modifySymbolsList": {
                return this.onModifySymbolsList(parameterMap);
            }
            case "modifySymbols": {
                return this.onModifySymbols(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onListProjects() throws Exception {
        JSONObject response = new JSONObject();
        List projects = ProjectEngine.list();
        projects.sort(this.projectNameComparator);
        JSONArray projectsArray = new JSONArray();
        for (SQProject project : projects) {
            if (project.isAppProject()) continue;
            projectsArray.put((Object)project.getInfo());
        }
        response.put("projects", (Object)projectsArray);
        response.put("success", (Object)L.t((String)"Projects listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCreateProject(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName"});
        JSONObject response = new JSONObject();
        String projectName = TMProjectsServlet.normalizeProjectName(args.get("projectName")[0]);
        TMProjectsServlet.validateProjectName(projectName);
        if (ProjectEngine.projectExists((String)projectName)) {
            throw new Exception(L.t((String)"Project with the same name already exists.", (Object[])new Object[0]));
        }
        SQProject project = ProjectEngine.add((String)projectName);
        response.put("success", (Object)L.t((String)"Project created %s.", (Object[])new Object[]{project.getName()}));
        response.put("projectName", (Object)project.getName());
        return response.toString();
    }

    private String onOpenProject(Map<String, String[]> args) throws Exception {
        String projectName;
        this.checkParamExists(args, new String[]{"file"});
        JSONObject response = new JSONObject();
        String projectFilePath = args.get("file")[0];
        boolean loadAsIs = false;
        if (!projectFilePath.endsWith(".cfx")) {
            projectFilePath = projectFilePath + ".cfx";
        }
        try {
            loadAsIs = Boolean.parseBoolean(args.get("loadAsIs")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        File projectFile = new File(projectFilePath);
        Element configXml = SQFileManager.loadProjectConfig((File)projectFile);
        if (!configXml.getName().equals("Project")) {
            return TMProjectsServlet.apiErrorJSON((String)L.t((String)"Cannot load config. Selected config is not a project template", (Object[])new Object[0]), null);
        }
        if (args.containsKey("projectName")) {
            configXml.setAttribute("name", TMProjectsServlet.normalizeProjectName(this.getParam(args, "projectName")[0]));
        }
        if ((projectName = TMProjectsServlet.normalizeProjectName(configXml.getAttributeValue("name"))) == null) {
            return TMProjectsServlet.apiErrorJSON((String)L.t((String)"Corrupted Project config file. Missing project name.", (Object[])new Object[0]), null);
        }
        TMProjectsServlet.validateProjectName(projectName);
        HashMap taskConfigs = null;
        if (loadAsIs) {
            if (SQProject.projectIsOlderThan136((Element)configXml)) {
                taskConfigs = SQFileManager.convertOldProjectConfig((Element)configXml);
            }
            SQProject project = ProjectEngine.add((String)projectName, (File)projectFile, (Element)configXml, (HashMap)taskConfigs);
            response.put("success", (Object)String.format("Project loaded '%s'.", project.getName()));
            response.put("projectName", (Object)project.getName());
        } else {
            Element resources = ProjectResources.checkProjectResources((File)projectFile, (Element)configXml);
            if (resources == null) {
                if (SQProject.projectIsOlderThan136((Element)configXml)) {
                    taskConfigs = SQFileManager.convertOldProjectConfig((Element)configXml);
                }
                SQProject project = ProjectEngine.add((String)projectName, (File)projectFile, (Element)configXml, (HashMap)taskConfigs);
                response.put("success", (Object)L.t((String)"Project loaded '%s'.", (Object[])new Object[]{project.getName()}));
                response.put("projectName", (Object)project.getName());
            } else {
                response.put("configXML", (Object)XMLUtil.elementToString((Element)configXml));
                response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)resources));
                response.put("success", (Object)L.t((String)"Resources info returned.", (Object[])new Object[0]));
                projectName = ProjectEngine.generateProjectName((String)projectName);
                response.put("projectName", (Object)projectName);
            }
        }
        return response.toString();
    }

    private String onValidateProject(Map<String, String[]> args) throws Exception {
        try {
            File projectFile;
            this.checkParamExists(args, new String[]{"filePath"});
            String filePath = this.getParam(args, "filePath")[0];
            if (!filePath.endsWith(".cfx")) {
                filePath = filePath + ".cfx";
            }
            if (!(projectFile = new File(filePath)).isFile()) {
                JSONObject verdict = new JSONObject();
                verdict.put("valid", false);
                verdict.put("stage", (Object)"resolve");
                verdict.put("error", (Object)("No such file: " + filePath));
                verdict.put("success", (Object)"ok");
                return verdict.toString();
            }
            boolean deep = true;
            try {
                deep = Boolean.parseBoolean(args.get("deep")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            boolean settings = true;
            try {
                settings = Boolean.parseBoolean(args.get("settings")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            JSONObject verdict = ProjectFileValidator.validate((File)projectFile, (boolean)deep, (boolean)settings);
            verdict.put("success", (Object)"ok");
            return verdict.toString();
        }
        catch (Exception e) {
            return TMProjectsServlet.apiErrorJSON((String)L.t((String)"Validation failed.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onSaveProject(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "file"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String projectFile = args.get("file")[0];
        if (!projectFile.endsWith(".cfx")) {
            projectFile = projectFile + ".cfx";
        }
        SQProject project = ProjectEngine.get((String)projectName);
        SQFileManager.saveProjectFile((SQProject)project, (File)new File(projectFile));
        response.put("success", (Object)L.t((String)"Project saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveProject(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        ProjectEngine.remove((String)projectName);
        response.put("success", (Object)L.t((String)"Project removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRenameProject(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"oldName", "newName"});
        JSONObject response = new JSONObject();
        String oldName = args.get("oldName")[0];
        String newName = TMProjectsServlet.normalizeProjectName(args.get("newName")[0]);
        TMProjectsServlet.validateProjectName(newName);
        ProjectEngine.rename((String)oldName, (String)newName);
        response.put("success", (Object)L.t((String)"Project renamed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCloneProject(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        SQProject sourceProject = ProjectEngine.get((String)projectName);
        Element config = sourceProject.getConfig();
        SQProject newProject = ProjectEngine.add((String)projectName, (File)sourceProject.getProjectConfigFile(), (Element)config.clone(), null);
        newProject.getDatabanks().loadStrategies();
        response.put("success", (Object)L.t((String)"Project cloned.", (Object[])new Object[0]));
        return response.toString();
    }

    private static String normalizeProjectName(String projectName) {
        return projectName == null ? null : projectName.trim();
    }

    private static void validateProjectName(String projectName) throws Exception {
        if (projectName == null || projectName.isEmpty()) {
            throw new Exception(L.t((String)"Project name cannot be empty.", (Object[])new Object[0]));
        }
        if (projectName.startsWith(".")) {
            throw new Exception(L.t((String)"Project name cannot start with dot.", (Object[])new Object[0]));
        }
        if (FORBIDDEN_PROJECT_NAME_CHARS.matcher(projectName).find()) {
            throw new Exception(L.t((String)"Project name contains forbidden characters: \\ / : * ? \" < > |", (Object[])new Object[0]));
        }
        if (RESERVED_PROJECT_NAME.matcher(projectName).matches()) {
            throw new Exception(L.t((String)"Project name uses a reserved system name.", (Object[])new Object[0]));
        }
        for (int i = 0; i < projectName.length(); ++i) {
            char c = projectName.charAt(i);
            if (!Character.isWhitespace(c) || c == ' ') continue;
            throw new Exception(L.t((String)"Project name cannot contain tabs or new lines.", (Object[])new Object[0]));
        }
    }

    private String onAddTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName", "taskType"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        String taskType = args.get("taskType")[0];
        int index = -1;
        try {
            index = Integer.parseInt(args.get("index")[0]);
        }
        catch (Exception exception) {
            // empty catch block
        }
        SQProject project = ProjectEngine.get((String)projectName);
        this.tryUpdateProjectConfig(project, args);
        ISQTask newTask = project.addTask(taskName, taskType, index);
        if (newTask == null) {
            return TMProjectsServlet.apiErrorJSON((String)L.t((String)"Task not created. Please check task with the same name doesn't already exist.", (Object[])new Object[0]), null);
        }
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("taskXML", (Object)XMLUtil.elementToString((Element)newTask.getConfig()));
        response.put("taskXMLFile", (Object)newTask.getTaskXMLFileName());
        response.put("success", (Object)L.t((String)"Task added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        this.tryUpdateProjectConfig(project, args);
        ISQTask removedTask = project.removeTask(taskName);
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("taskXMLFile", (Object)removedTask.getTaskXMLFileName());
        response.put("success", (Object)L.t((String)"Task removed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetAvailableTasks() throws Exception {
        JSONObject response = new JSONObject();
        JSONArray tasks = new JSONArray();
        for (ISQTask task : SQPluginManager.getPlugins(ISQTask.class)) {
            if (task.getType().equals("NeuralNetworkTrainer")) continue;
            tasks.put((Object)new JSONObject().put("type", (Object)task.getType()).put("name", (Object)task.getName()));
        }
        response.put("tasks", (Object)tasks);
        response.put("success", (Object)L.t((String)"Available tasks listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onMoveTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName", "toIndex"});
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        int toIndex = Integer.parseInt(args.get("toIndex")[0]);
        SQProject project = ProjectEngine.get((String)projectName);
        if (project == null) {
            throw new Exception(L.t((String)"Project with name '%s' does not exist.", (Object[])new Object[]{projectName}));
        }
        this.tryUpdateProjectConfig(project, args);
        project.moveTask(taskName, toIndex);
        JSONObject response = new JSONObject();
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("success", (Object)L.t((String)"Task moved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRenameTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName", "taskTitle"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        String taskTitle = args.get("taskTitle")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        this.tryUpdateProjectConfig(project, args);
        project.setTaskTitle(taskName, taskTitle);
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("success", (Object)L.t((String)"Task renamed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onCloneTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        SQProject project = ProjectEngine.get((String)projectName);
        this.tryUpdateProjectConfig(project, args);
        String position = this.getParam(args, "position", "end");
        ISQTask task = project.cloneTask(taskName, position);
        response.put("taskType", (Object)task.getType());
        response.put("taskName", (Object)task.getName());
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("xmlConfig", (Object)XMLUtil.xmlToStringRaw((Element)project.getConfig()));
        response.put("taskXML", (Object)XMLUtil.elementToString((Element)task.getConfig()));
        response.put("taskXMLFile", (Object)task.getTaskXMLFileName());
        response.put("success", (Object)L.t((String)"Task cloned.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onActivateTask(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "taskName", "active"});
        JSONObject response = new JSONObject();
        String projectName = args.get("projectName")[0];
        String taskName = args.get("taskName")[0];
        boolean active = Boolean.parseBoolean(args.get("active")[0]);
        SQProject project = ProjectEngine.get((String)projectName);
        this.tryUpdateProjectConfig(project, args);
        project.setTaskActive(taskName, active);
        response.put("success", (Object)L.t((String)"Task status changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private void tryUpdateProjectConfig(SQProject project, Map<String, String[]> args) {
        try {
            String projectXML = args.get("projectXML")[0];
            if (projectXML != null) {
                Element projectConfig = XMLUtil.stringToElement((String)projectXML);
                project.updateConfig(projectConfig);
            }
        }
        catch (Exception e) {
            Log.warn("Saving project config failed", (Throwable)e);
        }
    }

    private String onModifySymbolsList(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName"});
        String projectName = args.get("projectName")[0];
        JSONObject response = new JSONObject();
        ArrayList<String> symbols = new ArrayList<String>();
        SQProject project = ProjectEngine.get((String)projectName);
        for (ISQTask task : project.getTasks()) {
            Element elSettings = task.getConfig();
            Element elData = elSettings.getChild("Data");
            if (elData == null) continue;
            this.parseSymbols(elData, symbols);
            Element elCrossChecks = XMLUtil.tryAddElement((Element)elSettings, (String)"CrossChecks");
            Element elAd = XMLUtil.tryAddElement((Element)elCrossChecks, (String)"RetestOnAdditionalMarkets");
            Element elAdSettings = XMLUtil.tryAddElement((Element)elAd, (String)"Settings");
            if (elAdSettings == null) continue;
            try {
                this.parseSymbols(elAdSettings, symbols);
            }
            catch (Exception e) {
                Log.debug("Error while modifying symbols. Exc.", (Throwable)e);
            }
        }
        JSONArray symbolsJSON = new JSONArray();
        for (String s : symbols) {
            symbolsJSON.put((Object)s);
        }
        response.put("symbols", (Object)symbolsJSON);
        response.put("success", (Object)L.t((String)"Symbols listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onModifySymbols(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"projectName", "symbols"});
        String projectName = args.get("projectName")[0];
        JSONArray symbolsInput = new JSONArray(args.get("symbols")[0]);
        JSONArray symbols = new JSONArray();
        for (int j = 0; j < symbolsInput.length(); ++j) {
            JSONObject item = symbolsInput.getJSONObject(j);
            if (!item.has("symbolFrom") || !item.has("symbolTo") || item.isNull("symbolFrom") || item.isNull("symbolTo")) continue;
            String symbolFrom = item.getString("symbolFrom");
            String symbolTo = item.getString("symbolTo");
            if (symbolFrom == null || symbolTo == null) continue;
            if (!symbolFrom.contains("/") || !symbolTo.contains("/")) {
                throw new Exception(L.t((String)"Symbols must be in format SYMBOL/TF.", (Object[])new Object[0]));
            }
            String sFrom = symbolFrom.split("/")[0].trim();
            String tfFrom = symbolFrom.split("/")[1].trim();
            String sTo = symbolTo.split("/")[0].trim();
            String tfTo = symbolTo.split("/")[1].trim();
            if (!sFrom.equals("*") && DataManager.getDataInfo((String)"History", (String)sFrom) == null) {
                throw new Exception(L.t((String)"Symbol with name '%s' doesn't exist.", (Object[])new Object[]{sFrom}));
            }
            if (!sTo.equals("*") && DataManager.getDataInfo((String)"History", (String)sTo) == null) {
                throw new Exception(L.t((String)"Symbol with name '%s' doesn't exist.", (Object[])new Object[]{sTo}));
            }
            if (!tfFrom.equals("*") && !TimeframeManager.TFExists((String)tfFrom)) {
                throw new Exception(L.t((String)"Timeframe '%s' doesn't exist.", (Object[])new Object[]{tfFrom}));
            }
            if (!tfTo.equals("*") && !TimeframeManager.TFExists((String)tfTo)) {
                throw new Exception(L.t((String)"Timeframe '%s' doesn't exist.", (Object[])new Object[]{tfTo}));
            }
            symbols.put((Object)item);
        }
        if (symbols.length() == 0) {
            throw new Exception(L.t((String)"No symbols to change.", (Object[])new Object[0]));
        }
        ArrayList<String> resources = new ArrayList<String>();
        JSONObject response = new JSONObject();
        SQProject project = ProjectEngine.get((String)projectName);
        for (int a = 0; a < project.getTasks().size(); ++a) {
            ISQTask task = project.getTask(a);
            Element elSettings = task.getConfig();
            Element elData = elSettings.getChild("Data");
            if (elData == null) continue;
            this.modifySymbols(elSettings, elData, symbols, resources);
            Element elCrossChecks = XMLUtil.tryAddElement((Element)elSettings, (String)"CrossChecks");
            Element elAd = XMLUtil.tryAddElement((Element)elCrossChecks, (String)"RetestOnAdditionalMarkets");
            Element elAdSettings = XMLUtil.tryAddElement((Element)elAd, (String)"Settings");
            if (elAdSettings == null) continue;
            try {
                this.modifySymbols(elSettings, elAdSettings, symbols, resources);
            }
            catch (Exception e) {
                Log.debug("Error while modifying symbols. Exc.", (Throwable)e);
            }
            Element elOptions = elSettings.getChild("Options");
            this.updateSessions(elOptions, symbols);
            ProjectResources.addResources((ISQTask)task);
        }
        SQFileManager.updateWholeProjectConfig((SQProject)project);
        response.put("success", (Object)L.t((String)"Symbols changed.", (Object[])new Object[0]));
        return response.toString();
    }

    private void updateSessions(Element elOptions, JSONArray symbols) {
        Element elParams;
        Element elBuildTradingOptions = elOptions == null ? null : elOptions.getChild("BuildTradingOptions");
        Element element = elParams = elBuildTradingOptions == null ? null : elBuildTradingOptions.getChild("Params");
        if (elParams == null) {
            return;
        }
        Element elMarketOpenSession = null;
        for (Element elParam : elParams.getChildren("Param")) {
            if (!"MarketOpenSession".equals(elParam.getAttributeValue("key"))) continue;
            elMarketOpenSession = elParam;
            break;
        }
        if (elMarketOpenSession == null) {
            return;
        }
        String currentSession = elMarketOpenSession.getTextTrim();
        if (currentSession == null || currentSession.isEmpty()) {
            return;
        }
        for (int j = 0; j < symbols.length(); ++j) {
            String sessionFrom;
            JSONObject item = symbols.getJSONObject(j);
            if (!item.has("symbolFrom") || !item.has("symbolTo") || item.isNull("symbolFrom") || item.isNull("symbolTo")) continue;
            String symbolFrom = item.getString("symbolFrom");
            String symbolTo = item.getString("symbolTo");
            if (symbolFrom == null || symbolTo == null || !symbolFrom.contains("/") || !symbolTo.contains("/")) continue;
            String sFrom = symbolFrom.split("/")[0].trim();
            String sTo = symbolTo.split("/")[0].trim();
            if (sFrom.equals("*") || sTo.equals("*") || (sessionFrom = this.resolveMarketOpenSessionForSymbol(sFrom)) == null || !currentSession.equals(sessionFrom)) continue;
            String sessionTo = this.resolveMarketOpenSessionForSymbol(sTo);
            if (sessionTo != null && !sessionTo.equals(currentSession)) {
                elMarketOpenSession.setText(sessionTo);
            }
            return;
        }
    }

    private String resolveMarketOpenSessionForSymbol(String symbol) {
        ArrayList sessions;
        String instrumentDescription;
        if (symbol == null || symbol.isEmpty()) {
            return null;
        }
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
        if (dataInfo == null) {
            return null;
        }
        String instrumentName = dataInfo.instrument;
        String string = instrumentDescription = dataInfo.symbolInfo != null ? dataInfo.symbolInfo.description : null;
        if ((instrumentDescription == null || instrumentDescription.isEmpty()) && instrumentName != null) {
            try {
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)instrumentName);
                if (instrumentInfo != null) {
                    instrumentDescription = instrumentInfo.description;
                }
            }
            catch (Exception e) {
                Log.debug("Unable to resolve instrument description for session remap. Instrument: {}", (Object)instrumentName, (Object)e);
            }
        }
        if ((sessions = SessionManager.getSessions()) == null || sessions.isEmpty()) {
            return null;
        }
        if (instrumentName != null && !instrumentName.isEmpty()) {
            for (Session session : sessions) {
                if (!instrumentName.equals(session.getSessionName())) continue;
                return session.getSessionName();
            }
        }
        if (instrumentDescription != null && !instrumentDescription.isEmpty()) {
            for (Session session : sessions) {
                String sessionName = session.getSessionName();
                if (sessionName == null || !sessionName.startsWith(instrumentDescription)) continue;
                return sessionName;
            }
        }
        return null;
    }

    private void parseSymbols(Element el, List<String> symbols) {
        String mainSymbol = null;
        String mainTimeframe = null;
        Element elSetups = el.getChild("Setups");
        List setupEls = elSetups.getChildren("Setup");
        for (int s = 0; s < setupEls.size(); ++s) {
            Element elSetup = (Element)setupEls.get(s);
            List subchartEls = elSetup.getChildren("Chart");
            for (int i = 0; i < subchartEls.size(); ++i) {
                String tmp;
                if (i == 0) {
                    mainSymbol = ((Element)subchartEls.get(i)).getAttributeValue("symbol");
                    mainTimeframe = ((Element)subchartEls.get(i)).getAttributeValue("timeframe");
                    tmp = mainSymbol + "/" + mainTimeframe;
                } else {
                    String symbol = ((Element)subchartEls.get(i)).getAttributeValue("symbol");
                    String timeframe = ((Element)subchartEls.get(i)).getAttributeValue("timeframe");
                    if (symbol.equals("Same as main chart")) {
                        symbol = mainSymbol;
                    }
                    if (timeframe.equals("Same as main data")) {
                        timeframe = mainTimeframe;
                    }
                    tmp = symbol + "/" + timeframe;
                }
                if (symbols.contains(tmp)) continue;
                symbols.add(tmp);
            }
        }
    }

    private void updateSpreadInCrossCheckRetestHigherPrecision(Element elSettings, double spread) throws JDOMException, IOException {
        Element crossCheckEl = elSettings.getChild("CrossChecks");
        if (crossCheckEl == null) {
            return;
        }
        Element retestEl = crossCheckEl.getChild("RetestWithHigherPrecision");
        if (retestEl == null) {
            return;
        }
        Element settingsEl = retestEl.getChild("Settings");
        if (settingsEl == null) {
            return;
        }
        boolean customSpread = XMLUtil.getBoolean((Element)settingsEl, (String)"CustomSpread", (boolean)false);
        if (customSpread) {
            return;
        }
        Element elSpread = XMLUtil.stringToElement((String)("<Spread>" + spread + "</Spread>"));
        settingsEl.removeChild("Spread");
        settingsEl.addContent((Content)elSpread);
    }

    private void modifySymbols(Element elSettings, Element el, JSONArray symbols, List<String> resources) throws Exception {
        Element elSetups = el.getChild("Setups");
        List setupEls = elSetups.getChildren("Setup");
        for (int s = 0; s < setupEls.size(); ++s) {
            Element elSetup = (Element)setupEls.get(s);
            String mainSymbol = null;
            String mainTimeframe = null;
            List subchartEls = elSetup.getChildren("Chart");
            for (int i = 0; i < subchartEls.size(); ++i) {
                String timeframe;
                String symbol;
                Element elChart = (Element)subchartEls.get(i);
                if (i == 0) {
                    mainSymbol = elChart.getAttributeValue("symbol");
                    mainTimeframe = elChart.getAttributeValue("timeframe");
                    symbol = mainSymbol;
                    timeframe = mainTimeframe;
                } else {
                    symbol = elChart.getAttributeValue("symbol");
                    timeframe = elChart.getAttributeValue("timeframe");
                    if (symbol.equals("Same as main chart")) {
                        symbol = mainSymbol;
                    }
                    if (timeframe.equals("Same as main data")) {
                        timeframe = mainTimeframe;
                    }
                }
                for (int j = 0; j < symbols.length(); ++j) {
                    JSONObject item = symbols.getJSONObject(j);
                    if (!item.has("symbolFrom") || !item.has("symbolTo") || item.isNull("symbolFrom") || item.isNull("symbolTo")) continue;
                    String symbolFrom = item.getString("symbolFrom");
                    String symbolTo = item.getString("symbolTo");
                    boolean applyDefaultSettings = item.getBoolean("applyDefaultSettings");
                    if (symbolFrom == null || symbolTo == null || !symbolFrom.contains("/") || !symbolTo.contains("/")) continue;
                    String sFrom = symbolFrom.split("/")[0].trim();
                    String tfFrom = symbolFrom.split("/")[1].trim();
                    String sTo = symbolTo.split("/")[0].trim();
                    String tfTo = symbolTo.split("/")[1].trim();
                    if (sFrom.equals("*")) {
                        sFrom = symbol;
                    }
                    if (tfFrom.equals("*")) {
                        tfFrom = timeframe;
                    }
                    if (sTo.equals("*")) {
                        sTo = symbol;
                    }
                    if (tfTo.equals("*")) {
                        tfTo = timeframe;
                    }
                    if (!symbol.equals(sFrom) || !timeframe.equals(tfFrom)) continue;
                    elChart.setAttribute("symbol", sTo);
                    elChart.setAttribute("timeframe", tfTo);
                    if (applyDefaultSettings) {
                        DataInfo di = DataManager.getDataInfo((String)"History", (String)sTo);
                        elChart.setAttribute("spread", di.symbolInfo.defaultSpread + "");
                        elSetup.setAttribute("slippage", di.symbolInfo.defaultSlippage + "");
                        try {
                            Element elCommMethod = XMLUtil.stringToElement((String)di.symbolInfo.commissions);
                            elSetup.getChild("Commissions").removeContent();
                            elSetup.getChild("Commissions").addContent((Content)elCommMethod);
                        }
                        catch (Exception e) {
                            throw new Exception(L.t((String)"Error while applying default commission.", (Object[])new Object[0]) + " " + e.getMessage(), e);
                        }
                        try {
                            if (di.symbolInfo.swap != null) {
                                Element elSwap = XMLUtil.stringToElement((String)di.symbolInfo.swap);
                                elSetup.removeChild("Swap");
                                elSetup.addContent((Content)elSwap);
                            }
                        }
                        catch (Exception e) {
                            throw new Exception(L.t((String)"Error while applying default swap.", (Object[])new Object[0]) + " " + e.getMessage(), e);
                        }
                        if (i == 0) {
                            this.updateSpreadInCrossCheckRetestHigherPrecision(elSettings, di.symbolInfo.defaultSpread);
                        }
                    }
                    if (resources.contains(sTo)) continue;
                    resources.add(sTo);
                }
            }
        }
    }
}

