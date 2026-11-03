/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.HistoryDataLoader
 *  com.strategyquant.lib.HistoryDataNotAvailableExeption
 *  com.strategyquant.lib.HistoryOHLCData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.license.LicenseConstants
 *  com.strategyquant.lib.license.Licenser
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.StrategySaver
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.file.FileHandler
 *  com.strategyquant.tradinglib.strategy.SizingMetadata
 *  com.strategyquant.webguilib.server.AbstractUIWebServer
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.Plugins;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.HistoryDataLoader;
import com.strategyquant.lib.HistoryDataNotAvailableExeption;
import com.strategyquant.lib.HistoryOHLCData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.license.LicenseConstants;
import com.strategyquant.lib.license.Licenser;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.StrategySaver;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.file.FileHandler;
import com.strategyquant.tradinglib.strategy.SizingMetadata;
import com.strategyquant.webguilib.server.AbstractUIWebServer;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.IOException;
import java.nio.file.CopyOption;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResultsPluginsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ResultsPluginsServlet.class);
    private static final String LOCK_RESULTS_PLUGINS = "ResultsPlugins";
    private static IResultsGroupProvider rgProvider;
    private static final int CUSTOM_PLUGINS_LIMIT_STARTER = 0;
    private static final int CUSTOM_PLUGINS_LIMIT_PRO = 3;
    private static final Map<String, String> FORMAT_TO_TYPE;

    public ResultsPluginsServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "list": {
                return this.listPlugins(args);
            }
            case "create": {
                return this.createPlugin(args);
            }
            case "rename": {
                return this.renamePlugin(args);
            }
            case "delete": {
                return this.deletePlugin(args);
            }
            case "stats": {
                return this.getStats(args);
            }
            case "orders": {
                return this.getOrders(args);
            }
            case "settings": {
                return this.getLastSettingsXml(args);
            }
            case "databankStrategies": {
                return this.getDatabankStrategies(args);
            }
            case "strategyStats": {
                return this.getStrategyStats(args);
            }
            case "strategyOrders": {
                return this.getStrategyOrders(args);
            }
            case "strategyResultKeys": {
                return this.getStrategyResultKeys(args);
            }
            case "candles": {
                return this.getCandles(args);
            }
            case "dataSymbols": {
                return this.getDataSymbols(args);
            }
            case "strategyXml": {
                return this.getStrategyXml(args);
            }
            case "strategySourceCode": {
                return this.getStrategySourceCode(args);
            }
            case "saveStrategyFile": {
                return this.saveStrategyFile(args);
            }
        }
        return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private String listPlugins(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            JSONObject pluginJSON;
            File pluginsFolder = new File(SQStructure.USER_EXTEND_RESULTS_PLUGINS);
            ArrayList<String> defaultNames = new ArrayList<String>();
            List<String> customNames = new ArrayList();
            File[] plugins = pluginsFolder.listFiles();
            if (plugins != null) {
                for (File plugin : plugins) {
                    String name;
                    File indexFile;
                    if (!plugin.isDirectory() || plugin.getName().endsWith(".json") || !(indexFile = new File(plugin, "index.html")).exists() || (name = plugin.getName()).equals("CustomPlugin")) continue;
                    if (name.equals("Prop analytics") || name.equals("Prop Monte Carlo")) {
                        defaultNames.add(name);
                        continue;
                    }
                    customNames.add(name);
                }
            }
            Collections.sort(defaultNames);
            Collections.sort(customNames);
            int edition = Licenser.getInstance().getLicenseEdition();
            if (edition == LicenseConstants.EDITION_STARTER) {
                if (!customNames.isEmpty()) {
                    Log.info("ResultsPlugins: {} custom plugin(s) found but not loaded - Starter plan does not allow custom plugins.", (Object)customNames.size());
                }
                customNames.clear();
            } else if (edition == LicenseConstants.EDITION_PROFESIONAL && customNames.size() > 3) {
                Log.info("ResultsPlugins: {} custom plugin(s) found, loading only first {} - Pro plan limit.", (Object)customNames.size(), (Object)3);
                customNames = customNames.subList(0, 3);
            }
            JSONArray pluginsArray = new JSONArray();
            String appUrl = AbstractUIWebServer.getAppUrl();
            for (String name : defaultNames) {
                pluginJSON = new JSONObject();
                pluginJSON.put("name", (Object)name);
                pluginJSON.put("url", (Object)(appUrl + "/plugins/" + name + "/index.html"));
                pluginJSON.put("isDefault", true);
                pluginsArray.put((Object)pluginJSON);
            }
            for (String name : customNames) {
                pluginJSON = new JSONObject();
                pluginJSON.put("name", (Object)name);
                pluginJSON.put("url", (Object)(appUrl + "/plugins/" + name + "/index.html"));
                pluginJSON.put("isDefault", false);
                pluginsArray.put((Object)pluginJSON);
            }
            response.put("plugins", (Object)pluginsArray);
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to load results plugins.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)"Plugins listed");
        return response.toString();
    }

    private String renamePlugin(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String pluginName = this.getParam(args, "pluginName", null);
            String newName = this.getParam(args, "newName", null);
            if (pluginName == null || newName == null || newName.trim().isEmpty()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin name and new name are required.", (Object[])new Object[0]), null);
            }
            pluginName = pluginName.trim();
            if (!(newName = newName.trim()).matches("^[a-zA-Z0-9_\\s-]+$") || newName.contains("..") || newName.contains("/") || newName.contains("\\")) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Invalid plugin name.", (Object[])new Object[0]), null);
            }
            File pluginsFolder = new File(SQStructure.USER_EXTEND_RESULTS_PLUGINS);
            File oldDir = new File(pluginsFolder, pluginName);
            File newDir = new File(pluginsFolder, newName);
            if (!oldDir.isDirectory()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin not found.", (Object[])new Object[0]), null);
            }
            if (newDir.exists()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"A plugin with this name already exists.", (Object[])new Object[0]), null);
            }
            Files.move(oldDir.toPath(), newDir.toPath(), new CopyOption[0]);
            response.put("success", (Object)L.t((String)"Plugin renamed.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to rename plugin.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String deletePlugin(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String pluginName = this.getParam(args, "pluginName", null);
            if (pluginName == null || pluginName.trim().isEmpty()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin name is required.", (Object[])new Object[0]), null);
            }
            if ((pluginName = pluginName.trim()).contains("..") || pluginName.contains("/") || pluginName.contains("\\")) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Invalid plugin name.", (Object[])new Object[0]), null);
            }
            if (pluginName.equals("CustomPlugin")) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Cannot delete template plugin.", (Object[])new Object[0]), null);
            }
            File pluginsFolder = new File(SQStructure.USER_EXTEND_RESULTS_PLUGINS);
            File pluginDir = new File(pluginsFolder, pluginName);
            if (!pluginDir.isDirectory()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin not found.", (Object[])new Object[0]), null);
            }
            this.deleteRecursively(pluginDir);
            response.put("success", (Object)L.t((String)"Plugin removed.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to remove plugin.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private void deleteRecursively(File f) throws IOException {
        File[] children;
        if (f.isDirectory() && (children = f.listFiles()) != null) {
            for (File c : children) {
                this.deleteRecursively(c);
            }
        }
        Files.delete(f.toPath());
    }

    private int countCustomPlugins(File pluginsFolder) {
        int count = 0;
        File[] plugins = pluginsFolder.listFiles();
        if (plugins != null) {
            for (File plugin : plugins) {
                String name;
                if (!plugin.isDirectory() || plugin.getName().endsWith(".json") || !new File(plugin, "index.html").exists() || (name = plugin.getName()).equals("CustomPlugin") || name.equals("Prop analytics") || name.equals("Prop Monte Carlo")) continue;
                ++count;
            }
        }
        return count;
    }

    private String createPlugin(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            File templateFolder;
            File templateIndex;
            String pluginName = this.getParam(args, "pluginName", null);
            if (pluginName == null || pluginName.trim().isEmpty()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin name is required.", (Object[])new Object[0]), null);
            }
            if (!(pluginName = pluginName.trim()).matches("^[a-zA-Z0-9_\\s-]+$")) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Plugin name may only contain letters, numbers, spaces, hyphens and underscores.", (Object[])new Object[0]), null);
            }
            if (pluginName.contains("..") || pluginName.contains("/") || pluginName.contains("\\")) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Invalid plugin name.", (Object[])new Object[0]), null);
            }
            int edition = Licenser.getInstance().getLicenseEdition();
            if (edition == LicenseConstants.EDITION_STARTER) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Custom plugins are not available in the Starter plan. Upgrade to Pro or Ultimate to use this feature.", (Object[])new Object[0]), null);
            }
            File pluginsFolder = new File(SQStructure.USER_EXTEND_RESULTS_PLUGINS);
            if (edition == LicenseConstants.EDITION_PROFESIONAL) {
                int currentCount = this.countCustomPlugins(pluginsFolder);
                Log.info("ResultsPlugins createPlugin: currentCount={}, limit={}", (Object)currentCount, (Object)3);
                if (currentCount >= 3) {
                    Log.warn("ResultsPlugins: Pro plan limit reached ({} plugins), blocking creation of '{}'.", (Object)currentCount, (Object)pluginName);
                    return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Custom plugin limit reached. Pro plan allows up to %d custom plugins. Upgrade to Ultimate for unlimited plugins.", (Object[])new Object[]{3}), null);
                }
            }
            if (!(templateIndex = new File(templateFolder = new File(pluginsFolder, "CustomPlugin"), "index.html")).exists()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Custom Plugin template not found.", (Object[])new Object[0]), null);
            }
            File newPluginFolder = new File(pluginsFolder, pluginName);
            if (newPluginFolder.exists()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"A plugin with this name already exists.", (Object[])new Object[0]), null);
            }
            if (!newPluginFolder.mkdirs()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to create plugin folder.", (Object[])new Object[0]), null);
            }
            File newIndex = new File(newPluginFolder, "index.html");
            Files.copy(templateIndex.toPath(), newIndex.toPath(), StandardCopyOption.REPLACE_EXISTING);
            response.put("success", (Object)L.t((String)"Plugin created.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to create plugin.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStats(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(args, LOCK_RESULTS_PLUGINS);
            String resultkey = this.getParam(args, "resultKey", "Portfolio");
            byte direction = Byte.parseByte(this.getParam(args, "direction", "0"));
            byte sampleType = Byte.parseByte(this.getParam(args, "sampleType", "127"));
            byte plType = Byte.parseByte(this.getParam(args, "plType", "10"));
            Result result = resultsGroup.subResult(resultkey);
            if (result == null) {
                throw new Exception("Result not found");
            }
            SQStats stats = result.statsOrNull(direction, plType, sampleType);
            if (stats == null) {
                throw new Exception("Stats not found");
            }
            JSONObject statsJSON = this.buildStatsJSON(stats, plType);
            response.put("stats", (Object)statsJSON);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy stats failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getOrders(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(args, LOCK_RESULTS_PLUGINS);
            String resultkey = this.getParam(args, "resultKey", "Portfolio");
            byte direction = Byte.parseByte(this.getParam(args, "direction", "0"));
            byte sampleType = Byte.parseByte(this.getParam(args, "sampleType", "127"));
            OrdersList orders = resultsGroup.orders().filterExcludingControlOrders(resultkey, direction, sampleType, true);
            JSONArray ordersArray = this.buildOrdersJSON(orders);
            response.put("orders", (Object)ordersArray);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy orders failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getLastSettingsXml(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(args, LOCK_RESULTS_PLUGINS);
            response.put("lastSettingsXml", (Object)resultsGroup.getLastSettings());
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy orders failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String getDatabankStrategies(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            if (projectName == null || databankName == null) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName and databankName are required.", (Object[])new Object[0]), null);
            }
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            ArrayList records = databank.getRecords();
            JSONArray strategies = new JSONArray();
            for (int i = 0; i < records.size(); ++i) {
                strategies.put((Object)((ResultsGroup)records.get(i)).getName());
            }
            response.put("strategies", (Object)strategies);
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to list databank strategies.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStrategyResultKeys(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            if (projectName == null || databankName == null || strategyName == null) {
                String string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName and strategyName are required.", (Object[])new Object[0]), null);
                return string;
            }
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            List keys = resultsGroup.getResultKeys();
            JSONArray keysArray = new JSONArray();
            for (String key : keys) {
                keysArray.put((Object)key);
            }
            response.put("resultKeys", (Object)keysArray);
            response.put("strategyName", (Object)strategyName);
        }
        catch (Exception e) {
            String string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to get strategy result keys.", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStrategyStats(Map<String, String[]> args) {
        String string;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            if (projectName == null || databankName == null || strategyName == null) {
                String string2 = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName and strategyName are required.", (Object[])new Object[0]), null);
                return string2;
            }
            String resultkey = this.getParam(args, "resultKey", "Portfolio");
            byte direction = Byte.parseByte(this.getParam(args, "direction", "0"));
            byte sampleType = Byte.parseByte(this.getParam(args, "sampleType", "127"));
            byte plType = Byte.parseByte(this.getParam(args, "plType", "10"));
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            Result result = resultsGroup.subResult(resultkey);
            if (result == null) {
                throw new Exception("Result not found");
            }
            SQStats stats = result.statsOrNull(direction, plType, sampleType);
            if (stats == null) {
                throw new Exception("Stats not found");
            }
            JSONObject statsJSON = this.buildStatsJSON(stats, plType);
            response.put("strategyName", (Object)strategyName);
            response.put("stats", (Object)statsJSON);
        }
        catch (RecordNotFoundException e) {
            Log.info("getStrategyStats: " + e.getMessage());
            string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy stats failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStrategyOrders(Map<String, String[]> args) {
        String string;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            if (projectName == null || databankName == null || strategyName == null) {
                String string2 = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName and strategyName are required.", (Object[])new Object[0]), null);
                return string2;
            }
            String resultkey = this.getParam(args, "resultKey", "Portfolio");
            byte direction = Byte.parseByte(this.getParam(args, "direction", "0"));
            byte sampleType = Byte.parseByte(this.getParam(args, "sampleType", "127"));
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            OrdersList orders = resultsGroup.orders().filterExcludingControlOrders(resultkey, direction, sampleType, true);
            JSONArray ordersArray = this.buildOrdersJSON(orders);
            response.put("strategyName", (Object)strategyName);
            response.put("orders", (Object)ordersArray);
        }
        catch (RecordNotFoundException e) {
            Log.info("getStrategyOrders: " + e.getMessage());
            string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy orders failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String getCandles(Map<String, String[]> args) {
        try {
            int count;
            String symbol = this.getParam(args, "symbol", null);
            String timeframe = this.getParam(args, "timeframe", null);
            String dateFromStr = this.getParam(args, "dateFrom", null);
            String dateToStr = this.getParam(args, "dateTo", null);
            String session = this.getParam(args, "session", "No Session");
            int maxBars = Integer.parseInt(this.getParam(args, "maxBars", "50000"));
            if (symbol == null || symbol.isEmpty()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Parameter 'symbol' is required.", (Object[])new Object[0]), null);
            }
            if (timeframe == null || timeframe.isEmpty()) {
                return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Parameter 'timeframe' is required.", (Object[])new Object[0]), null);
            }
            long dateFrom = 0L;
            long dateTo = Long.MAX_VALUE;
            if (dateFromStr != null && !dateFromStr.isEmpty()) {
                dateFrom = Long.parseLong(dateFromStr);
            }
            if (dateToStr != null && !dateToStr.isEmpty()) {
                dateTo = Long.parseLong(dateToStr);
            }
            HistoryOHLCData data = HistoryDataLoader.get((String)symbol, (String)timeframe, (long)dateFrom, (long)dateTo, (String)session);
            int n = count = data.Time != null ? data.Time.length : 0;
            if (count > maxBars) {
                int offset = count - maxBars;
                long[] time = new long[maxBars];
                float[] open = new float[maxBars];
                float[] high = new float[maxBars];
                float[] low = new float[maxBars];
                float[] close = new float[maxBars];
                float[] volume = new float[maxBars];
                System.arraycopy(data.Time, offset, time, 0, maxBars);
                System.arraycopy(data.Open, offset, open, 0, maxBars);
                System.arraycopy(data.High, offset, high, 0, maxBars);
                System.arraycopy(data.Low, offset, low, 0, maxBars);
                System.arraycopy(data.Close, offset, close, 0, maxBars);
                System.arraycopy(data.Volume, offset, volume, 0, maxBars);
                data.Time = time;
                data.Open = open;
                data.High = high;
                data.Low = low;
                data.Close = close;
                data.Volume = volume;
                count = maxBars;
            }
            JSONObject json = new JSONObject();
            json.put("success", (Object)"ok");
            json.put("symbol", (Object)symbol);
            json.put("timeframe", (Object)timeframe);
            json.put("count", count);
            JSONArray timeArr = new JSONArray();
            JSONArray openArr = new JSONArray();
            JSONArray highArr = new JSONArray();
            JSONArray lowArr = new JSONArray();
            JSONArray closeArr = new JSONArray();
            JSONArray volArr = new JSONArray();
            for (int i = 0; i < count; ++i) {
                timeArr.put(data.Time[i]);
                openArr.put((double)data.Open[i]);
                highArr.put((double)data.High[i]);
                lowArr.put((double)data.Low[i]);
                closeArr.put((double)data.Close[i]);
                volArr.put((double)data.Volume[i]);
            }
            json.put("time", (Object)timeArr);
            json.put("open", (Object)openArr);
            json.put("high", (Object)highArr);
            json.put("low", (Object)lowArr);
            json.put("close", (Object)closeArr);
            json.put("volume", (Object)volArr);
            return json.toString();
        }
        catch (HistoryDataNotAvailableExeption e) {
            String msg = e.getMessage();
            StringBuilder chain = new StringBuilder(msg != null ? msg : "unknown");
            for (Throwable cause = e.getCause(); cause != null; cause = cause.getCause()) {
                String causeMsg = cause.getMessage();
                if (causeMsg == null || causeMsg.isEmpty()) continue;
                chain.append(" -> ").append(cause.getClass().getSimpleName()).append(": ").append(causeMsg);
            }
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"History data not available: %s", (Object[])new Object[]{chain.toString()}), (Throwable)e);
        }
        catch (Exception e) {
            String msg = e.getMessage();
            StringBuilder chain = new StringBuilder(msg != null ? msg : "unknown");
            for (Throwable cause = e.getCause(); cause != null; cause = cause.getCause()) {
                String causeMsg = cause.getMessage();
                if (causeMsg == null || causeMsg.isEmpty()) continue;
                chain.append(" -> ").append(cause.getClass().getSimpleName()).append(": ").append(causeMsg);
            }
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to load candle data: %s", (Object[])new Object[]{chain.toString()}), (Throwable)e);
        }
    }

    private String getDataSymbols(Map<String, String[]> args) {
        JSONObject json = new JSONObject();
        try {
            ArrayList dataInfoList = DataManager.list();
            JSONArray symbolsArr = new JSONArray();
            for (DataInfo di : dataInfoList) {
                JSONObject sym = new JSONObject();
                sym.put("symbol", (Object)di.symbol);
                sym.put("timeframe", (Object)di.timeframe);
                sym.put("dateFrom", di.dateFrom);
                sym.put("dateTo", di.dateTo);
                sym.put("decimals", di.decimals);
                sym.put("rows", di.rows);
                symbolsArr.put((Object)sym);
            }
            json.put("symbols", (Object)symbolsArr);
        }
        catch (Exception e) {
            return ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Failed to list data symbols: %s", (Object[])new Object[]{e.getMessage()}), (Throwable)e);
        }
        json.put("success", (Object)"ok");
        return json.toString();
    }

    private JSONObject buildStatsJSON(SQStats stats, byte plType) {
        JSONObject statsJSON = new JSONObject();
        statsJSON.put("NetProfit", stats.getDouble("NetProfit"));
        statsJSON.put("NumberOfTrades", stats.getInt("NumberOfTrades"));
        String dd_key = plType == 20 ? "DrawdownPct" : (plType == 30 ? "DrawdownPips" : "Drawdown");
        statsJSON.put("Drawdown", stats.getDouble(dd_key));
        statsJSON.put("PctDrawdown", stats.getDouble("DrawdownPct"));
        statsJSON.put("PipsDrawdown", stats.getDouble("DrawdownPips"));
        statsJSON.put("AvgProfitByDay", stats.getDouble("AvgProfitPerDay"));
        statsJSON.put("AvgProfitByMonth", stats.getDouble("AvgProfitPerMonth"));
        statsJSON.put("AvgProfitByYear", stats.getDouble("AvgProfitPerYear"));
        statsJSON.put("AvgPctProfitByYear", stats.getDouble("AvgPctProfitPerYear"));
        statsJSON.put("AvgTrade", stats.getDouble("AvgTrade"));
        statsJSON.put("AvgAbsTrade", stats.getDouble("AvgAbsTrade"));
        statsJSON.put("AvgTradesPerDay", stats.getDouble("AvgTradesPerDay"));
        statsJSON.put("AvgTradesPerMonth", stats.getDouble("AvgTradesPerMonth"));
        statsJSON.put("AvgTradesPerYear", stats.getDouble("AvgTradesPerYear"));
        statsJSON.put("ProfitFactor", stats.getDouble("ProfitFactor"));
        statsJSON.put("SharpeRatio", stats.getDouble("SharpeRatio"));
        statsJSON.put("Stability", stats.getDouble("Stability"));
        statsJSON.put("Symmetry", stats.getDouble("Symmetry"));
        statsJSON.put("ReturnDDRatio", stats.getDouble("ReturnDDRatio"));
        statsJSON.put("ReturnOpenDDRatio", stats.getDouble("ReturnOpenDDRatio"));
        statsJSON.put("AAR_DD_Ratio", stats.getDouble("AnnualPctReturnDDRatio"));
        statsJSON.put("CalmarRatio", stats.getDouble("CalmarRatio"));
        statsJSON.put("RExpectancy", stats.getDouble("RExpectancy"));
        statsJSON.put("RExpectancyScore", stats.getDouble("RExpectancyScore"));
        statsJSON.put("SQN", stats.getDouble("SQN"));
        statsJSON.put("SQNScore", stats.getDouble("SQNScore"));
        statsJSON.put("WinLossRatio", stats.getDouble("WinLossRatio"));
        statsJSON.put("WinningPct", stats.getDouble("WinningPct"));
        statsJSON.put("PayoutRatio", stats.getDouble("PayoutRatio"));
        statsJSON.put("AvgBarsTrade", stats.getDouble("AvgBarsInTrade"));
        statsJSON.put("AHPR", stats.getDouble("AHPR"));
        statsJSON.put("ZScore", stats.getDouble("ZScore"));
        statsJSON.put("ZProbability", stats.getDouble("ZProbability"));
        statsJSON.put("Expectancy", stats.getDouble("Expectancy"));
        statsJSON.put("StandardDev", stats.getDouble("StandardDev"));
        statsJSON.put("Exposure", stats.getDouble("Exposure", 0.0));
        statsJSON.put("ExposurePosition", stats.getDouble("ExposurePosition", 0.0));
        statsJSON.put("StagnationPeriod", stats.getInt("Stagnation"));
        statsJSON.put("StagnationPeriodPct", stats.getDouble("StagnationPct"));
        statsJSON.put("StagnationFrom", stats.getInt("StagnationFrom"));
        statsJSON.put("StagnationTo", stats.getInt("StagnationTo"));
        statsJSON.put("DegreesOfFreedom", stats.getInt("DegreesOfFreedom"));
        statsJSON.put("NumberOfProfits", stats.getInt("NumberOfProfits"));
        statsJSON.put("NumberOfLosses", stats.getInt("NumberOfLosses"));
        statsJSON.put("NumberOfCanceled", stats.getInt("NumberOfCanceled"));
        statsJSON.put("GrossProfit", stats.getDouble("GrossProfit"));
        statsJSON.put("GrossLoss", stats.getDouble("GrossLoss"));
        statsJSON.put("AvgWin", stats.getDouble("AvgWin"));
        statsJSON.put("AvgLoss", stats.getDouble("AvgLoss"));
        statsJSON.put("MaxProfit", stats.getDouble("MaxProfit"));
        statsJSON.put("MaxLoss", stats.getDouble("MaxLoss"));
        statsJSON.put("MaxConsecWins", stats.getInt("MaxConsecWins"));
        statsJSON.put("MaxConsecLoss", stats.getInt("MaxConsecLosses"));
        statsJSON.put("AvgConsecWin", stats.getDouble("AvgConsecWins"));
        statsJSON.put("AvgConsecLoss", stats.getDouble("AvgConsecLosses"));
        statsJSON.put("AvgBarsWin", stats.getDouble("AvgBarsWin"));
        statsJSON.put("AvgBarsLoss", stats.getDouble("AvgBarsLoss"));
        statsJSON.put("TotalTradingDays", stats.getInt("TotalTradingDays"));
        statsJSON.put("TotalTradingMonths", stats.getInt("TotalTradingMonths"));
        statsJSON.put("TotalTradingYears", stats.getInt("TotalTradingYears"));
        statsJSON.put("ProfitableMonths", stats.getInt("ProfitableMonths"));
        statsJSON.put("Commission", stats.getDouble("Commission"));
        statsJSON.put("SlippageInMoney", stats.getDouble("SlippageInMoney"));
        statsJSON.put("CommSwapInMoney", stats.getDouble("CommSwapInMoney"));
        statsJSON.put("NetProfitInPips", stats.getDouble("NetProfitInPips"));
        statsJSON.put("MaxNewHighDurationFrom", stats.getInt("MaxNewHighDurationFrom"));
        statsJSON.put("MaxNewHighDurationTo", stats.getInt("MaxNewHighDurationTo"));
        statsJSON.put("MaxNewHighDurationPeriod", stats.getInt("MaxNewHighDuration"));
        statsJSON.put("MaxNewHighDurationPct", stats.getDouble("MaxNewHighDurationPct"));
        return statsJSON;
    }

    private JSONArray buildOrdersJSON(OrdersList orders) {
        JSONArray ordersArray = new JSONArray();
        for (int i = 0; i < orders.size(); ++i) {
            Order order = orders.get(i);
            JSONObject orderJSON = new JSONObject();
            orderJSON.put("Ticket", order.Ticket);
            orderJSON.put("Symbol", (Object)order.Symbol);
            orderJSON.put("ResultName", (Object)order.SetupName);
            orderJSON.put("NumberOfTrade", order.Order);
            orderJSON.put("OpenTime", order.OpenTime);
            orderJSON.put("CloseTime", order.CloseTime);
            orderJSON.put("OriginalOpenTime", order.OriginalOpenTime);
            orderJSON.put("Type", (int)order.Type);
            orderJSON.put("CloseType", (int)order.CloseType);
            orderJSON.put("SampleType", (int)order.SampleType);
            orderJSON.put("OpenPrice", (double)order.OpenPrice);
            orderJSON.put("ClosePrice", (double)order.ClosePrice);
            orderJSON.put("OriginalOpenPrice", (double)order.OriginalPrice);
            orderJSON.put("SLLevel", (double)order.StopLoss);
            orderJSON.put("PTLevel", (double)order.TakeProfit);
            orderJSON.put("Size", (double)order.Size);
            orderJSON.put("BarsInTrade", (int)order.BarsInTrade);
            orderJSON.put("TimeInTrade", order.Duration);
            orderJSON.put("ProfitLoss", (double)order.PL);
            orderJSON.put("ProfitLossPct", (double)order.PctPL);
            orderJSON.put("ProfitLossPips", (double)order.PipsPL);
            orderJSON.put("Drawdown", (double)order.DD);
            orderJSON.put("PctDrawdown", (double)order.PctDD);
            orderJSON.put("MAE", (double)order.MAE);
            orderJSON.put("MAEPips", (double)order.PipsMAE);
            orderJSON.put("MFE", (double)order.MFE);
            orderJSON.put("MFEPips", (double)order.PipsMFE);
            orderJSON.put("Comment", (Object)order.Comment);
            orderJSON.put("CommSwap", (double)order.CommSwap);
            orderJSON.put("SlippageInMoney", (double)order.SlippageInMoney);
            orderJSON.put("Balance", (double)order.AccountBalance);
            ordersArray.put((Object)orderJSON);
        }
        return ordersArray;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStrategyXml(Map<String, String[]> args) {
        String string;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            if (projectName == null || databankName == null || strategyName == null) {
                String string2 = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName and strategyName are required.", (Object[])new Object[0]), null);
                return string2;
            }
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            Element strategyXml = resultsGroup.getStrategyXml();
            if (strategyXml == null) {
                throw new Exception("Strategy XML not found");
            }
            response.put("strategyName", (Object)strategyName);
            response.put("xml", (Object)XMLUtil.elementToString((Element)strategyXml));
        }
        catch (RecordNotFoundException e) {
            Log.info("getStrategyXml: " + e.getMessage());
            string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Getting strategy XML failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    static String sourceCodeOf(ResultsGroup resultsGroup, String strategyName, String fullType) throws Exception {
        Element rgEl = resultsGroup.getStrategyXml();
        if (rgEl == null) {
            throw new Exception("Strategy XML not found for '" + strategyName + "'");
        }
        rgEl = rgEl.clone();
        String lastSettings = resultsGroup.getLastSettings();
        SizingMetadata sizing = SizingMetadata.resolve((ResultsGroup)resultsGroup, (String)strategyName);
        StrategyBase xmlS = StrategyBase.createXmlStrategy((Element)rgEl);
        xmlS.transformToVariables(false, null);
        xmlS.variables().sortByName();
        String mmType = "fromStrategy";
        rgEl = StrategyXMLModifier.getUpdatedStrategyXML((ResultsGroup)resultsGroup, (Element)rgEl, (String)mmType, (String)strategyName, (String)lastSettings, null);
        if (StrategySaver.isMetaTraderGenerator((String)fullType)) {
            StrategySaver.normalizeExportSymbols((Element)rgEl);
        }
        XMLIndicatorsAnalyzer.init();
        XMLIndicatorsAnalyzer.fixItemAttributes((Element)rgEl);
        CustomDataManager.addCDataIndySourceCodes((Element)rgEl);
        CustomBlocks.addCBlockSourceCodes((Element)rgEl);
        SourceCodeGenerator sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName(fullType);
        if (sourceCodeGenerator == null) {
            throw new Exception("No source code generator found for type '" + fullType + "'");
        }
        Log.info("strategySourceCode: Generating {} for {}", (Object)sourceCodeGenerator.getName(), (Object)strategyName);
        return sourceCodeGenerator.getSource(strategyName, rgEl, sizing.orderSizeMultiplier, sizing.orderSizeStep, sizing.pointValue, sizing.barTimeType);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String getStrategySourceCode(Map<String, String[]> args) {
        String string;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            String type = this.getParam(args, "type", "mq5");
            if (projectName == null || databankName == null || strategyName == null) {
                String string2 = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName and strategyName are required.", (Object[])new Object[0]), null);
                return string2;
            }
            String fullType = FORMAT_TO_TYPE.containsKey(type) ? FORMAT_TO_TYPE.get(type) : SourceCodeGenerators.getInstance().canonicalize(type);
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            String code = ResultsPluginsServlet.sourceCodeOf(resultsGroup, strategyName, fullType);
            response.put("strategyName", (Object)strategyName);
            response.put("code", (Object)code);
        }
        catch (RecordNotFoundException e) {
            Log.info("getStrategySourceCode: " + e.getMessage());
            string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            Log.error("getStrategySourceCode failed", (Throwable)e);
            string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Generating source code failed for strategy", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String saveStrategyFile(Map<String, String[]> args) {
        String string;
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            String projectName = this.getParam(args, "projectName", null);
            String databankName = this.getParam(args, "databankName", null);
            String strategyName = this.getParam(args, "strategyName", null);
            String outputPath = this.getParam(args, "outputPath", null);
            if (projectName == null || databankName == null || strategyName == null || outputPath == null) {
                String string2 = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"projectName, databankName, strategyName and outputPath are required.", (Object[])new Object[0]), null);
                return string2;
            }
            File outputDir = new File(outputPath);
            if (!outputDir.exists()) {
                outputDir.mkdirs();
            }
            Databank databank = (Databank)ProjectEngine.get((String)projectName).getDatabanks().get((Object)databankName);
            resultsGroup = databank.getLocked(strategyName, LOCK_RESULTS_PLUGINS);
            String safeFileName = strategyName.replaceAll("[^a-zA-Z0-9_\\-\\.]", "_");
            String sqxFilePath = outputPath + File.separator + safeFileName + ".sqx";
            FileHandler fileHandler = new FileHandler();
            fileHandler.saveFile(resultsGroup, sqxFilePath, null);
            Log.info("saveStrategyFile: Saved {} to {}", (Object)strategyName, (Object)sqxFilePath);
            response.put("strategyName", (Object)strategyName);
            response.put("path", (Object)sqxFilePath);
        }
        catch (RecordNotFoundException e) {
            Log.info("saveStrategyFile: " + e.getMessage());
            string = ResultsPluginsServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            Log.error("saveStrategyFile failed", (Throwable)e);
            string = ResultsPluginsServlet.apiErrorJSON((String)L.t((String)"Saving strategy file failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_RESULTS_PLUGINS);
                resultsGroup = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    static {
        FORMAT_TO_TYPE = new HashMap<String, String>();
        FORMAT_TO_TYPE.put("mq5", SourceCodeGenerator.MetaTrader5);
        FORMAT_TO_TYPE.put("mq4", SourceCodeGenerator.MetaTrader4);
        FORMAT_TO_TYPE.put("pseudo", SourceCodeGenerator.PseudoCode);
        FORMAT_TO_TYPE.put("el", SourceCodeGenerator.EasyLanguage);
        FORMAT_TO_TYPE.put("java", SourceCodeGenerator.JForex);
        FORMAT_TO_TYPE.put("xml", SourceCodeGenerator.StrategyXML);
        FORMAT_TO_TYPE.put("nt8", SourceCodeGenerator.NinjaTrader);
    }
}

