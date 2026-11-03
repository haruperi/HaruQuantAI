/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sqxbusiness.MQLMarketConst
 *  com.strategyquant.lib.sqxbusiness.SQXBusinessMainSettings
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.Variable
 *  com.strategyquant.tradinglib.Variables
 *  com.strategyquant.tradinglib.optimization.Parameter
 *  com.strategyquant.tradinglib.optimization.ParametersSettings
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.strategy.SizingMetadata
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.apache.commons.io.FileUtils
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.App.impl.SQXBusiness;

import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sqxbusiness.MQLMarketConst;
import com.strategyquant.lib.sqxbusiness.SQXBusinessMainSettings;
import com.strategyquant.plugin.App.impl.SQXBusiness.EAParameters;
import com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketBuildExecutor;
import com.strategyquant.plugin.App.impl.SQXBusiness.MQLMarketProjects;
import com.strategyquant.plugin.App.impl.SQXBusiness.SQXBusinessBuildReporter;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Variable;
import com.strategyquant.tradinglib.Variables;
import com.strategyquant.tradinglib.optimization.Parameter;
import com.strategyquant.tradinglib.optimization.ParametersSettings;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.strategy.SizingMetadata;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.IOException;
import java.util.Base64;
import java.util.Map;
import org.apache.commons.io.FileUtils;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQXBusinessServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SQXBusinessServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        if (!(command.equals("listProjects") || command.equals("loadMainSettings") || MainApp.getLicenseInfo().isUltimateEdition() && !MainApp.getLicenseInfo().isFutlab())) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"SQX business functionality is available for ultimate users only!", (Object[])new Object[0]), null);
        }
        switch (command) {
            case "checkFileExists": {
                return this.onCheckFileExists(parameterMap);
            }
            case "loadMainSettings": {
                return this.onLoadMainSettings();
            }
            case "saveMainSettings": {
                return this.onSaveMainSettings(parameterMap);
            }
            case "listProjects": {
                return this.onListProjects();
            }
            case "addProject": {
                return this.onAddProject(parameterMap);
            }
            case "updateProject": {
                return this.onUpdateProject(parameterMap);
            }
            case "removeProject": {
                return this.onRemoveProject(parameterMap);
            }
            case "uploadStrategyFile": {
                return this.onUploadStrategyFile(parameterMap);
            }
            case "uploadLogo": {
                return this.onUploadLogo(parameterMap);
            }
            case "uploadResource": {
                return this.onUploadResource(parameterMap);
            }
            case "deleteResource": {
                return this.onDeleteResource(parameterMap);
            }
            case "loadParameters": {
                return this.onLoadParameters(parameterMap);
            }
            case "loadEAOptions": {
                return this.onLoadEAOptions(parameterMap);
            }
            case "clearLog": {
                return this.onClearLog(parameterMap);
            }
            case "build": {
                return this.onBuild(parameterMap);
            }
            case "stop": {
                return this.onStop(parameterMap);
            }
            case "pause": {
                return this.onPause(parameterMap);
            }
            case "resume": {
                return this.onResume(parameterMap);
            }
        }
        throw new Exception(L.t((String)"Unknown command '%s'.", (Object[])new Object[]{command}));
    }

    private String onCheckFileExists(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"path"});
        String path = this.tryGetParamValue(parameterMap, "path");
        return new JSONObject().put("success", (Object)L.t((String)"File checked", (Object[])new Object[0])).put("exists", new File(path).exists()).toString();
    }

    private String onLoadMainSettings() {
        JSONObject response = new JSONObject();
        response.put("mt4Path", (Object)SQXBusinessMainSettings.getMT4Path());
        response.put("mt5Path", (Object)SQXBusinessMainSettings.getMT5Path());
        return response.toString();
    }

    private String onSaveMainSettings(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"mt4Path", "mt5Path"});
        String mt4Path = this.tryGetParamValue(parameterMap, "mt4Path");
        String mt5Path = this.tryGetParamValue(parameterMap, "mt5Path");
        try {
            SQXBusinessMainSettings.save((String)mt4Path, (String)mt5Path);
            return new JSONObject().put("success", (Object)L.t((String)"Settings saved", (Object[])new Object[0])).toString();
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while saving settings", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onListProjects() {
        JSONObject response = new JSONObject();
        try {
            JSONArray projects = new JSONArray();
            for (String key : MQLMarketProjects.list().keySet()) {
                JSONObject project = new JSONObject();
                project.put("name", (Object)key);
                project.put("config", (Object)XMLUtil.elementToString((Element)MQLMarketProjects.list().get(key)));
                projects.put((Object)project);
            }
            response.put("projects", (Object)projects);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while loading SQX Business projects", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Projects listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddProject(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"name", "config"});
        try {
            String name = this.tryGetParamValue(parameterMap, "name");
            String config = this.tryGetParamValue(parameterMap, "config");
            MQLMarketProjects.add(name, XMLUtil.stringToElement((String)config));
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot add project", (Object[])new Object[0]), (Throwable)e);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Project added", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateProject(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"name", "config"});
        try {
            String name = this.tryGetParamValue(parameterMap, "name");
            String config = this.tryGetParamValue(parameterMap, "config");
            String oldName = null;
            try {
                oldName = this.tryGetParamValue(parameterMap, "oldName");
            }
            catch (Exception exception) {
                // empty catch block
            }
            MQLMarketProjects.update(name, XMLUtil.stringToElement((String)config), oldName);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot update project", (Object[])new Object[0]), (Throwable)e);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Project updated", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRemoveProject(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"name"});
        try {
            String name = this.tryGetParamValue(parameterMap, "name");
            MQLMarketProjects.remove(name);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot update project", (Object[])new Object[0]), (Throwable)e);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Project removed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUploadStrategyFile(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"fileName", "file", "projectName"});
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String fileName = this.tryGetParamValue(parameterMap, "fileName");
        String fileDataStr = this.tryGetParamValue(parameterMap, "file");
        try {
            byte[] decodedData = Base64.getDecoder().decode(fileDataStr.getBytes());
            String projectFolder = MQLMarketConst.getProjectDirPath((String)projectName);
            String filePath = projectFolder + "/" + fileName;
            File[] files = new File(projectFolder).listFiles();
            for (int a = 0; a < files.length; ++a) {
                File file = files[a];
                String subfileName = file.getName();
                if (file.isDirectory() || subfileName.equals("config.xml") || subfileName.startsWith("logo") || subfileName.endsWith("ex4") || subfileName.endsWith("ex5")) continue;
                file.delete();
            }
            FileUtils.writeByteArrayToFile((File)new File(filePath), (byte[])decodedData);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Uploading file failed", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onUploadLogo(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"fileName", "file", "projectName"});
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String fileName = this.tryGetParamValue(parameterMap, "fileName");
        String fileDataStr = this.tryGetParamValue(parameterMap, "file");
        try {
            String fileExtension = SQUtils.getExtension((String)fileName);
            String logoFileName = "logo." + fileExtension;
            byte[] decodedData = Base64.getDecoder().decode(fileDataStr.getBytes());
            String projectFolder = MQLMarketConst.getProjectDirPath((String)projectName);
            String filePath = projectFolder + "/" + logoFileName;
            File[] files = new File(projectFolder).listFiles();
            for (int a = 0; a < files.length; ++a) {
                File file = files[a];
                String subfileName = file.getName();
                if (file.isDirectory() || !subfileName.startsWith("logo")) continue;
                file.delete();
            }
            FileUtils.writeByteArrayToFile((File)new File(filePath), (byte[])decodedData);
            response.put("success", (Object)L.t((String)"Logo saved", (Object[])new Object[0]));
            response.put("logoSrc", (Object)("data:image/png;base64," + fileDataStr));
        }
        catch (IOException e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Uploading file failed", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onUploadResource(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"fileName", "file", "projectName"});
        JSONObject response = new JSONObject();
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String fileName = this.tryGetParamValue(parameterMap, "fileName");
        String fileDataStr = this.tryGetParamValue(parameterMap, "file");
        String oldResource = "";
        try {
            oldResource = this.tryGetParamValue(parameterMap, "oldResource");
        }
        catch (Exception exception) {
            // empty catch block
        }
        try {
            File newResourceFile;
            byte[] decodedData = Base64.getDecoder().decode(fileDataStr.getBytes());
            String resourcesDirPath = MQLMarketConst.getProjectDirPath((String)projectName) + "/resources";
            if (!oldResource.isEmpty()) {
                new File(resourcesDirPath + "/" + oldResource).delete();
            }
            if ((newResourceFile = new File(resourcesDirPath + "/" + fileName)).exists()) {
                throw new Exception(L.t((String)"File '%s' already exists<br>Please delete the old resource or choose another file", (Object[])new Object[]{fileName}));
            }
            newResourceFile.getParentFile().mkdirs();
            FileUtils.writeByteArrayToFile((File)newResourceFile, (byte[])decodedData);
            response.put("success", (Object)L.t((String)"Resource saved", (Object[])new Object[0]));
        }
        catch (IOException e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Uploading resource failed", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onDeleteResource(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"resourceName", "projectName"});
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String resourceName = this.tryGetParamValue(parameterMap, "resourceName");
        String resourcesDirPath = MQLMarketConst.getProjectDirPath((String)projectName);
        File resourceFile = new File(resourcesDirPath + "/resources/" + resourceName);
        if (resourceFile.exists() && !resourceFile.delete()) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Unable to delete resource file from disk", (Object[])new Object[0]), null);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Resource file deleted", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadParameters(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"fileName", "projectName"});
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String fileName = this.tryGetParamValue(parameterMap, "fileName");
        String projectFolder = MQLMarketConst.getProjectDirPath((String)projectName);
        String strategyFilePath = projectFolder + "/" + fileName;
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Parameters loaded", (Object[])new Object[0]));
        try {
            if (!new File(strategyFilePath).exists()) {
                throw new Exception(L.t((String)"Strategy file doesn't exist", (Object[])new Object[0]));
            }
            Element elProject = MQLMarketProjects.list().get(projectName);
            if (elProject == null) {
                throw new Exception(L.t((String)"Project config not found", (Object[])new Object[0]));
            }
            JSONArray variables = new JSONArray();
            StrategyBase strBase = EAParameters.getStrategyBase(elProject);
            if (strBase != null) {
                Variables vars = strBase.variables();
                vars.sortByName();
                for (int a = 0; a < vars.size(); ++a) {
                    Variable var = (Variable)vars.get(a);
                    byte type = var.getInternalType();
                    String name = var.getName();
                    String value = var.getValue();
                    if (type == 3 || name.contains("EntrySignal") || name.contains("ExitSignal") || name.contains("ReplaceExistingOrders") || type == 0 || name.equals("MagicNumber")) continue;
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
            }
            response.put("variables", (Object)variables);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot load strategy parameters", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onLoadEAOptions(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"projectName", "fileName"});
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String fileName = this.tryGetParamValue(parameterMap, "fileName");
        String projectFolder = MQLMarketConst.getProjectDirPath((String)projectName);
        String strategyFilePath = projectFolder + "/" + fileName;
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"EA options loaded", (Object[])new Object[0]));
        try {
            if (!new File(strategyFilePath).exists()) {
                throw new Exception(L.t((String)"Strategy file doesn't exist", (Object[])new Object[0]));
            }
            String generatorName = SourceCodeGenerator.MetaTrader5;
            SourceCodeGenerator sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(generatorName);
            if (sourceCodeGenerator == null) {
                String message = L.t((String)"Source code generator '%s' not found", (Object[])new Object[]{generatorName});
                Log.error(message);
                throw new Exception(message);
            }
            ResultsGroup rg = (ResultsGroup)Program.get((String)"Loader").call("loadFile", new Object[]{strategyFilePath});
            Element elStrategyFile = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)rg);
            SizingMetadata sizing = SizingMetadata.resolve((ResultsGroup)rg, (String)rg.getName());
            String sourceCode = sourceCodeGenerator.getSource(rg.getName(), elStrategyFile, sizing.orderSizeMultiplier, sizing.orderSizeStep, sizing.pointValue, sizing.barTimeType);
            response.put("options", (Object)this.loadEAOptions(sourceCode));
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot load strategy options", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private JSONArray loadEAOptions(String sourceCode) throws Exception {
        JSONArray options = new JSONArray();
        int start = sourceCode.indexOf("string CustomComment");
        if (start < 0) {
            throw new Exception("Source code start point not found");
        }
        int end = sourceCode.indexOf("void OnTick()");
        if (end < 0) {
            throw new Exception("Source code end point not found");
        }
        String code = sourceCode.substring(start, end);
        String[] lines = code.split("\n");
        for (int i = 0; i < lines.length; ++i) {
            String line = lines[i].trim();
            if (!line.startsWith("input")) continue;
            String[] parts = line.split("=");
            if (parts.length != 2) {
                Log.error("Unrecognized EA option '" + line + "' - invalid parts length");
                continue;
            }
            String[] words = parts[0].split(" ");
            if (words.length != 3) {
                Log.error("Unrecognized EA option '" + line + "' - invalid words length");
                continue;
            }
            JSONObject option = new JSONObject();
            option.put("type", (Object)words[1]);
            option.put("name", (Object)words[2]);
            option.put("enabled", true);
            String value = parts[1].trim();
            int valueEndPos = value.indexOf(";");
            if (valueEndPos < 0) {
                Log.error("Unrecognized EA option '" + line + "' - ; not found");
                continue;
            }
            value = value.substring(0, valueEndPos);
            option.put("value", (Object)value.replace("\"", ""));
            options.put((Object)option);
        }
        return options;
    }

    private String onBuild(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"projectName", "type", "platform"});
        String projectName = this.tryGetParamValue(parameterMap, "projectName");
        String type = this.tryGetParamValue(parameterMap, "type");
        String platform = this.tryGetParamValue(parameterMap, "platform");
        try {
            Element elProject = MQLMarketProjects.list().get(projectName);
            if (elProject == null) {
                throw new Exception("Project config not found");
            }
            MQLMarketBuildExecutor.execute(projectName, elProject, type, platform);
            JSONObject response = new JSONObject();
            response.put("success", (Object)L.t((String)"Build job started", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Cannot build project", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onClearLog(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"jobID"});
        JSONObject response = new JSONObject();
        try {
            String jobID = this.tryGetParamValue(parameterMap, "jobID");
            SQXBusinessBuildReporter.clearLog(jobID);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while clearing log", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Log cleared", (Object[])new Object[0]));
        return response.toString();
    }

    private String onStop(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"jobGroupID", "jobID"});
        JSONObject response = new JSONObject();
        try {
            String jobGroupID = this.tryGetParamValue(parameterMap, "jobGroupID");
            String jobID = this.tryGetParamValue(parameterMap, "jobID");
            SQGrid.getGridClient().stop(jobGroupID, jobID);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while stopping build", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Build stopped", (Object[])new Object[0]));
        return response.toString();
    }

    private String onPause(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"jobGroupID", "jobID"});
        JSONObject response = new JSONObject();
        try {
            String jobGroupID = this.tryGetParamValue(parameterMap, "jobGroupID");
            String jobID = this.tryGetParamValue(parameterMap, "jobID");
            SQGrid.getGridClient().pause(jobGroupID, jobID);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while pausing build", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Build paused", (Object[])new Object[0]));
        return response.toString();
    }

    private String onResume(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"jobGroupID", "jobID"});
        JSONObject response = new JSONObject();
        try {
            String jobGroupID = this.tryGetParamValue(parameterMap, "jobGroupID");
            String jobID = this.tryGetParamValue(parameterMap, "jobID");
            SQGrid.getGridClient().restart(jobGroupID, jobID);
        }
        catch (Exception e) {
            return SQXBusinessServlet.apiErrorJSON((String)L.t((String)"Error while resuming build", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Build resumed", (Object[])new Object[0]));
        return response.toString();
    }
}

