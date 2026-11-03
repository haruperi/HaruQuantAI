/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.ailib.chat.SQAIBackendUrls
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.consts.Precisions
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.constants.SQPaths
 *  com.strategyquant.lib.snippets.compile.SQStructure
 *  com.strategyquant.lib.volumeProfile.VolumeProfileBlocks
 *  com.strategyquant.lib.volumeProfile.VolumeProfileSubscription
 *  com.strategyquant.pluginlib.program.IProgram
 *  com.strategyquant.pluginlib.program.Program
 *  com.strategyquant.tradinglib.ATM
 *  com.strategyquant.tradinglib.Blocks
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.CommissionsMethod
 *  com.strategyquant.tradinglib.IBlock
 *  com.strategyquant.tradinglib.MoneyManagementMethod
 *  com.strategyquant.tradinglib.NegatersList
 *  com.strategyquant.tradinglib.OverviewTemplate
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.RiskManagementMethod
 *  com.strategyquant.tradinglib.StatsTypeCombination
 *  com.strategyquant.tradinglib.StrategyBase
 *  com.strategyquant.tradinglib.SwapMethod
 *  com.strategyquant.tradinglib.atm.ATMConfigVerifier
 *  com.strategyquant.tradinglib.backtest.IBacktester
 *  com.strategyquant.tradinglib.backtest.SQBacktester
 *  com.strategyquant.tradinglib.backtest.StrategyFileBacktest
 *  com.strategyquant.tradinglib.backtestrunner.StrategyChecker
 *  com.strategyquant.tradinglib.blocks.CustomBlocks
 *  com.strategyquant.tradinglib.commissions.CommissionsMethodsList
 *  com.strategyquant.tradinglib.cot.CotSymbolResolver
 *  com.strategyquant.tradinglib.engine.ChartSetups
 *  com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction
 *  com.strategyquant.tradinglib.generator.Negaters
 *  com.strategyquant.tradinglib.generator.StrategyWithVariables
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.tradinglib.project.ProjectConfigHelper
 *  com.strategyquant.tradinglib.project.ProjectCustomResources
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.ProjectResources
 *  com.strategyquant.tradinglib.project.RandomGroups
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StrategySaver
 *  com.strategyquant.tradinglib.project.StrategyXMLModifier
 *  com.strategyquant.tradinglib.project.bestresults.BestResultOverview
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.overview.OverviewTemplates
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.strategy.OutOfSample
 *  com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter
 *  com.strategyquant.tradinglib.strategy.xml.StrategyFileValidator
 *  com.strategyquant.tradinglib.strategy.xml.StrategyFixer
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Content
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.AlgoWizard;

import com.strategyquant.ailib.chat.SQAIBackendUrls;
import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.consts.Precisions;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.constants.SQPaths;
import com.strategyquant.lib.snippets.compile.SQStructure;
import com.strategyquant.lib.volumeProfile.VolumeProfileBlocks;
import com.strategyquant.lib.volumeProfile.VolumeProfileSubscription;
import com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardBlocksTagCloud;
import com.strategyquant.plugin.Servlet.impl.AlgoWizard.AlgoWizardRecentFiles;
import com.strategyquant.pluginlib.program.IProgram;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.ATM;
import com.strategyquant.tradinglib.Blocks;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.IBlock;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.NegatersList;
import com.strategyquant.tradinglib.OverviewTemplate;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.SwapMethod;
import com.strategyquant.tradinglib.atm.ATMConfigVerifier;
import com.strategyquant.tradinglib.backtest.IBacktester;
import com.strategyquant.tradinglib.backtest.SQBacktester;
import com.strategyquant.tradinglib.backtest.StrategyFileBacktest;
import com.strategyquant.tradinglib.backtestrunner.StrategyChecker;
import com.strategyquant.tradinglib.blocks.CustomBlocks;
import com.strategyquant.tradinglib.commissions.CommissionsMethodsList;
import com.strategyquant.tradinglib.cot.CotSymbolResolver;
import com.strategyquant.tradinglib.engine.ChartSetups;
import com.strategyquant.tradinglib.fitnessfunction.IFitnessFunction;
import com.strategyquant.tradinglib.generator.Negaters;
import com.strategyquant.tradinglib.generator.StrategyWithVariables;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.ProjectCustomResources;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.ProjectResources;
import com.strategyquant.tradinglib.project.RandomGroups;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StrategySaver;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.project.bestresults.BestResultOverview;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.overview.OverviewTemplates;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import com.strategyquant.tradinglib.strategy.xml.SQ3StrategyConverter;
import com.strategyquant.tradinglib.strategy.xml.StrategyFileValidator;
import com.strategyquant.tradinglib.strategy.xml.StrategyFixer;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.file.Files;
import java.nio.file.StandardCopyOption;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.jar.JarEntry;
import java.util.jar.JarOutputStream;
import java.util.zip.ZipEntry;
import java.util.zip.ZipInputStream;
import java.util.zip.ZipOutputStream;
import org.jdom2.Content;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AlgoWizardServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(AlgoWizardServlet.class);
    public static final String VAR_ID_LONG_ENTRY = "33333333-1111-1111-3333-333333333333";
    public static final String VAR_ID_LONG_EXIT = "33333333-1111-2222-3333-333333333333";
    public static final String VAR_ID_SHORT_ENTRY = "33333333-2222-1111-3333-333333333333";
    public static final String VAR_ID_SHORT_EXIT = "33333333-2222-2222-3333-333333333333";
    private NegatersList negatersList = null;
    private IBacktester backtester;
    private IResultsGroupProvider rgProvider;
    private static final String RequestFailedFlag = "request-failed";
    private static boolean isBacktestNode;

    public AlgoWizardServlet(IBacktester backtester, IResultsGroupProvider rgProvider) {
        this.backtester = backtester;
        this.rgProvider = rgProvider;
        isBacktestNode = MainApp.isBacktestNode();
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        Log.debug("AW Request: " + command);
        if (command.startsWith("RESULTS")) {
            return this.onResults(command, parameterMap);
        }
        switch (command) {
            case "getConfig": {
                return this.onGetConfig(parameterMap);
            }
            case "loadFile": {
                return this.onLoadFile(parameterMap);
            }
            case "validate": {
                return this.onValidate(parameterMap);
            }
            case "backtestFile": {
                return this.onBacktestFile(parameterMap);
            }
            case "saveFile": {
                return this.onSaveFile(parameterMap);
            }
            case "saveToRetester": {
                return this.onSaveToRetester(parameterMap);
            }
            case "negate": {
                return this.onNegate(parameterMap);
            }
            case "negateCustomBlock": {
                return this.onNegateCustomBlock(parameterMap);
            }
            case "backtest": {
                return this.onBacktest(parameterMap);
            }
            case "stopBacktest": {
                return this.onStopBacktest(parameterMap);
            }
            case "addNewTimeframe": {
                return this.onAddNewTimeframe(parameterMap);
            }
            case "saveBlockToTagCloud": {
                return this.onSaveBlock(parameterMap);
            }
            case "loadExample": {
                return this.onLoadExample(parameterMap);
            }
            case "loadBlockGroups": {
                return this.onLoadBlockGroups(parameterMap);
            }
            case "saveBlockGroups": {
                return this.onSaveBlockGroups(parameterMap);
            }
            case "loadCustomBlocks": {
                return this.onLoadCustomBlocks(parameterMap);
            }
            case "saveCustomBlocks": {
                return this.onSaveCustomBlocks(parameterMap);
            }
            case "customDataIndys": {
                return this.onCustomDataIndys(parameterMap);
            }
            case "backupsCustomBlocks": {
                return this.onListBackupsCustomBlocks(parameterMap);
            }
            case "backupsBlockGroups": {
                return this.onListBackupsBlockGroups(parameterMap);
            }
            case "getBacktestResults": {
                return this.onGetBacktestResults(parameterMap);
            }
            case "checkResources": {
                return this.onCheckResources(parameterMap);
            }
            case "resolveResources": {
                return this.onResolveResources(parameterMap);
            }
            case "refreshResources": {
                return this.onRefreshResources(parameterMap);
            }
            case "resolveCotSymbols": {
                return this.onResolveCotSymbols(parameterMap);
            }
        }
        return AlgoWizardServlet.apiErrorJSON((String)("request-failedEndpoint 'algowizard' - command '" + command + "' not found"), null);
    }

    private String onCheckResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"strategyXML"});
        JSONObject response = new JSONObject();
        String strategyXML = this.tryGetParamValue(args, "strategyXML");
        String settingsXML = this.getParam(args, "settingsXML", null);
        try {
            Element config = XMLUtil.stringToElement((String)strategyXML);
            Element elStrategy = config.getChild("Strategy");
            Element elResources = ProjectCustomResources.checkStrategyResources((Element)elStrategy);
            if (settingsXML != null) {
                try {
                    Element settings = XMLUtil.stringToElement((String)settingsXML);
                    Element settingsResources = ProjectResources.checkTaskResources((Element)settings, (boolean)true);
                    if (settingsResources != null) {
                        List resChildren = settingsResources.getChildren();
                        for (int i = 0; i < resChildren.size(); ++i) {
                            elResources.addContent((Content)((Element)resChildren.get(i)).clone());
                        }
                    }
                }
                catch (Exception e) {
                    Log.error("Checking resources from settingsXML failed", (Throwable)e);
                }
            }
            response.put("success", (Object)L.t((String)"Custom resources checked.", (Object[])new Object[0]));
            response.put("resourcesXML", (Object)XMLUtil.elementToString((Element)elResources));
        }
        catch (Exception e) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot resolve resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onResolveResources(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"strategyXML", "resourcesXML"});
        JSONObject response = new JSONObject();
        String strategyXML = this.tryGetParamValue(args, "strategyXML");
        String resourcesXML = this.tryGetParamValue(args, "resourcesXML");
        String settingsXML = this.getParam(args, "settingsXML", null);
        try {
            Element strategy = XMLUtil.stringToElement((String)strategyXML);
            Element elResources = XMLUtil.stringToElement((String)resourcesXML);
            strategy = ProjectCustomResources.resolveStrategyResources((Element)elResources, (Element)strategy);
            Element settings = null;
            if (settingsXML != null) {
                settings = XMLUtil.stringToElement((String)settingsXML);
                JSONArray newSymbols = new JSONArray();
                boolean continueLoading = ProjectResources.resolveResources((Element)elResources, (Element)settings, null, (JSONArray)newSymbols, (Element)strategy);
                response.put("continueLoading", continueLoading);
                response.put("newSymbols", (Object)newSymbols);
                response.put("settingsXML", (Object)XMLUtil.elementToString((Element)settings));
            }
            response.put("strategyXML", (Object)XMLUtil.elementToString((Element)strategy));
            response.put("success", (Object)L.t((String)"Resources resolved.", (Object[])new Object[0]));
        }
        catch (Exception e) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot resolve resources.", (Object[])new Object[0]), (Throwable)e);
        }
        return response.toString();
    }

    private String onCustomDataIndys(Map<String, String[]> parameterMap) {
        String xml;
        JSONObject response = new JSONObject();
        try {
            File f = new File(SQPaths.algoWizardCustomDataIndysPath);
            xml = SQUtils.fileToString((File)f);
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot get CustomDataIndys.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("xml", (Object)xml);
        response.put("success", (Object)L.t((String)"CustomDataIndys loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    protected byte[] executeBinary(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        String file = null;
        try {
            if (command.endsWith("/")) {
                command = command.replaceFirst("/", "");
            }
            if (command.startsWith("RESULTS/webstatic")) {
                file = (command = command.replaceAll("RESULTS/webstatic", "")).contains("plugins/") ? MainApp.getDataPath() + command : MainApp.getDataPath() + "internal/web/" + command;
                return Files.readAllBytes(new File(file).toPath());
            }
            if (command.equals("RESULTS")) {
                command = command + "/index.html";
            }
            file = MainApp.getDataPath() + "internal/web/" + command;
            return Files.readAllBytes(new File(MainApp.getDataPath() + "internal/web/" + command).toPath());
        }
        catch (Exception e) {
            throw new Exception("request-failed -> Endpoint 'algowizard'. File not found: " + file);
        }
    }

    private String onResults(String command, Map<String, String[]> parameterMap) throws Exception {
        String file = null;
        try {
            if (command.endsWith("/")) {
                command = command.replaceFirst("/", "");
            }
            if (command.startsWith("RESULTS/webstatic")) {
                file = (command = command.replaceAll("RESULTS/webstatic", "")).contains("plugins/") ? MainApp.getDataPath() + command : MainApp.getDataPath() + "internal/web/" + command;
                return SQUtils.fileToString((String)file);
            }
            if (command.equals("RESULTS")) {
                command = command + "/index.html";
            }
            file = MainApp.getDataPath() + "internal/web/" + command;
            return SQUtils.fileToString((String)(MainApp.getDataPath() + "internal/web/" + command));
        }
        catch (Exception e) {
            Log.error("request-failed -> Endpoint 'algowizard'. File not found: " + file);
            return AlgoWizardServlet.apiErrorJSON((String)"request-failed -> File not found.", null);
        }
    }

    private String onGetConfig(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            response.put("wizardConfig", (Object)SQUtils.fileToString((File)new File(SQPaths.wizardConfigPath)));
            String initialStrategyConfigPath = SQStructure.INTERNAL_DIR_PATH + "web/" + "AlgoWizard" + "/assets/InitialStrategy.xml";
            response.put("initialStrategyConfig", (Object)SQUtils.fileToString((File)new File(initialStrategyConfigPath)));
            response.put("recentFiles", (Object)AlgoWizardRecentFiles.listJSON());
            response.put("blocksTagCloud", (Object)AlgoWizardBlocksTagCloud.listJSON());
            response.put("timeframes", (Object)WSDataObjects.getTimeframes((boolean)false).getDataArray());
            response.put("algoWizardType", (Object)System.getProperty("algoWizardType"));
            response.put("build", (Object)MainApp.getAppVersion());
            response.put("skins", (Object)this.getSkinList());
            try {
                response.put("zoom", Double.parseDouble(MainApp.settings().get("zoom")));
            }
            catch (Exception e) {
                response.put("zoom", 1.0);
            }
            JSONObject aiChatBackendUrls = SQAIBackendUrls.toJSON();
            if (aiChatBackendUrls.length() > 0) {
                response.put("aiChatBackendUrls", (Object)aiChatBackendUrls);
            }
            response.put("volumeProfile", (Object)VolumeProfileSubscription.toJSON());
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot get wizard config.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Config loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray getSkinList() {
        int a;
        JSONArray skins = new JSONArray();
        File pluginFolder = new File(SQStructure.PLUGINS_DIR);
        File[] folders = pluginFolder.listFiles();
        ArrayList<String> skinFilePaths = new ArrayList<String>();
        for (a = 0; a < folders.length; ++a) {
            File folder = folders[a];
            if (!folder.isDirectory() || !folder.getName().toLowerCase().startsWith("skin")) continue;
            String moduleJSPath = folder.getAbsolutePath() + "/module.js";
            skinFilePaths.add(moduleJSPath);
        }
        for (a = 0; a < skinFilePaths.size(); ++a) {
            File moduleFile = new File((String)skinFilePaths.get(a));
            if (!moduleFile.exists()) continue;
            try {
                int endIndex;
                int startIndex;
                String content = SQUtils.fileToString((File)moduleFile);
                int pluginDefIndex = content.indexOf("sqPluginProvider.plugin");
                if (pluginDefIndex < 0 || (startIndex = content.indexOf("{", pluginDefIndex)) < 0 || (endIndex = content.indexOf("}", startIndex)) < 0) continue;
                String pluginData = content.substring(startIndex, endIndex + 1);
                skins.put((Object)new JSONObject(pluginData));
                continue;
            }
            catch (Exception e) {
                Log.error("Loading skin plugin failed", (Throwable)e);
            }
        }
        return skins;
    }

    private String onLoadFile(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String filePath = this.tryGetParam(parameterMap, "filePath")[0];
            String extension = SQUtils.getExtension((String)filePath);
            if (extension.equals("sqw")) {
                Element elStrategy = XMLUtil.fileToXmlElement((File)new File(filePath));
                if (elStrategy != null) {
                    String version = elStrategy.getAttributeValue("version");
                    try {
                        if (version != null && Double.parseDouble(version) < 3.8) {
                            elStrategy = SQ3StrategyConverter.getInstance().convert(elStrategy);
                        }
                        elStrategy = StrategyFixer.fixStrategy((String)XMLUtil.elementToString((Element)elStrategy));
                    }
                    catch (Exception e) {
                        Log.error("Modifying XML config failed", (Throwable)e);
                    }
                }
                response.put("strategyConfig", (Object)XMLUtil.elementToString((Element)elStrategy));
            } else {
                IProgram loader = Program.get((String)"Loader");
                ResultsGroup resultsGroup = (ResultsGroup)loader.call("loadFile", new Object[]{filePath});
                Element elStrategyfile = resultsGroup.getStrategyXml();
                StrategyXMLModifier.addOptions((Element)elStrategyfile, (String)resultsGroup.getName(), (String)filePath);
                String strStrategy = XMLUtil.elementToString((Element)elStrategyfile);
                response.put("strategyConfig", (Object)strStrategy);
                response.put("lastSettings", (Object)resultsGroup.getLastSettings());
            }
            File f = new File(filePath);
            response.put("strategyName", (Object)SQUtils.stripExtension((String)new File(filePath).getName()));
            AlgoWizardRecentFiles.save(filePath);
            response.put("recentFiles", (Object)AlgoWizardRecentFiles.listJSON());
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Loading failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"File loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onValidate(Map<String, String[]> parameterMap) {
        try {
            String filePath = this.tryGetParam(parameterMap, "filePath")[0];
            File f = new File(filePath);
            if (!f.isFile()) {
                JSONObject verdict = new JSONObject();
                verdict.put("valid", false);
                verdict.put("stage", (Object)"resolve");
                verdict.put("error", (Object)("No such file: " + filePath));
                verdict.put("success", (Object)"ok");
                return verdict.toString();
            }
            JSONObject verdict = StrategyFileValidator.validate((File)f);
            verdict.put("success", (Object)"ok");
            return verdict.toString();
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Validation failed.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    private String onBacktestFile(Map<String, String[]> parameterMap) {
        try {
            String filePath = this.tryGetParam(parameterMap, "filePath")[0];
            File f = new File(filePath);
            if (!f.isFile()) {
                JSONObject out = new JSONObject();
                out.put("ok", false);
                out.put("error", (Object)("No such file: " + filePath));
                out.put("success", (Object)"ok");
                return out.toString();
            }
            JSONObject out = new StrategyFileBacktest().run((File)f).json;
            out.put("success", (Object)"ok");
            return out.toString();
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Backtest failed.", (Object[])new Object[0]), (Throwable)ex);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     * Enabled aggressive block sorting
     * Enabled unnecessary exception pruning
     * Enabled aggressive exception aggregation
     */
    private String onSaveFile(Map<String, String[]> parameterMap) {
        String filePath;
        JSONObject response;
        block29: {
            ZipEntry zipEntry;
            int bufferSize;
            byte[] buffer;
            ZipInputStream zip;
            ZipOutputStream jarOutStream;
            String lastSettings;
            String strategyConfig;
            block30: {
                response = new JSONObject();
                try {
                    boolean chooseFolder = Boolean.parseBoolean(this.tryGetParam(parameterMap, "chooseFolder")[0]);
                    strategyConfig = this.tryGetParam(parameterMap, "strategyConfig")[0];
                    String strategyName = this.getParam(parameterMap, "strategyName", null);
                    strategyConfig = SQUtils.xmlPrettyFormat((String)strategyConfig);
                    lastSettings = this.getParam(parameterMap, "lastSettings", null);
                    boolean isBacktested = false;
                    try {
                        isBacktested = Boolean.parseBoolean(this.tryGetParam(parameterMap, "backtested")[0]);
                    }
                    catch (Exception exception) {
                        // empty catch block
                    }
                    filePath = null;
                    if (chooseFolder) {
                        String defaultFolder = null;
                        try {
                            defaultFolder = this.tryGetParam(parameterMap, "defaultFolder")[0];
                        }
                        catch (Exception e) {
                            defaultFolder = MainApp.settings().containsKey("awSaveFile") ? MainApp.settings().get("awSaveFile") : SQPaths.projectsDirPath;
                        }
                        filePath = this.chooseFilePath(defaultFolder, strategyName);
                    } else {
                        filePath = this.tryGetParam(parameterMap, "filePath")[0];
                    }
                    if (filePath == null) {
                        throw new Exception("Saving canceled");
                    }
                    File outputFile = new File(filePath);
                    boolean fileExists = outputFile.exists();
                    if (!fileExists) {
                        outputFile.getParentFile().mkdirs();
                    }
                    jarOutStream = null;
                    zip = null;
                    File tempFile = null;
                    buffer = new byte[1024];
                    bufferSize = 0;
                    try {
                        String backtestID;
                        try {
                            if (isBacktested && this.backtester instanceof SQBacktester) {
                                backtestID = this.tryGetParam(parameterMap, "backtestID")[0];
                                SQBacktester.getResultsGroup((String)backtestID);
                            }
                        }
                        catch (Exception e) {
                            isBacktested = false;
                        }
                        if (isBacktested && this.backtester instanceof SQBacktester) {
                            backtestID = this.tryGetParam(parameterMap, "backtestID")[0];
                            ResultsGroup lastBacktest = SQBacktester.getResultsGroup((String)backtestID);
                            lastSettings = lastBacktest.getLastSettings();
                            lastSettings = this.addResources(lastSettings);
                            lastBacktest.setLastSettings(lastSettings);
                            StrategySaver saver = new StrategySaver();
                            saver.save(lastBacktest, "sqx", filePath, false, 0, parameterMap);
                            break block29;
                        }
                        lastSettings = this.addResources(lastSettings);
                        if (fileExists) {
                            tempFile = new File(filePath + "_temp");
                            Files.copy(outputFile.toPath(), tempFile.toPath(), StandardCopyOption.REPLACE_EXISTING);
                            zip = new ZipInputStream(new FileInputStream(tempFile));
                            jarOutStream = new JarOutputStream(new FileOutputStream(outputFile));
                            break block30;
                        }
                        jarOutStream = new JarOutputStream(new FileOutputStream(outputFile));
                        JarEntry entry = new JarEntry("strategy_Portfolio.xml");
                        ((JarOutputStream)jarOutStream).putNextEntry(entry);
                        jarOutStream.write(strategyConfig.getBytes("UTF8"));
                        if (lastSettings == null) break block29;
                        JarEntry entry2 = new JarEntry("lastSettings.xml");
                        ((JarOutputStream)jarOutStream).putNextEntry(entry2);
                        jarOutStream.write(lastSettings.getBytes("UTF8"));
                        break block29;
                    }
                    catch (Exception e) {
                        Log.error("Saving exception. ", (Throwable)e);
                        break block29;
                    }
                    finally {
                        if (jarOutStream != null) {
                            jarOutStream.close();
                        }
                        if (zip != null) {
                            zip.close();
                        }
                        if (tempFile != null) {
                            tempFile.delete();
                        }
                    }
                }
                catch (Exception ex) {
                    return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving failed.", (Object[])new Object[0]), (Throwable)ex);
                }
            }
            while ((zipEntry = zip.getNextEntry()) != null) {
                JarEntry entry;
                String name = zipEntry.getName();
                if (name.startsWith("strategy_Portfolio.xml")) {
                    entry = new JarEntry("strategy_Portfolio.xml");
                    ((JarOutputStream)jarOutStream).putNextEntry(entry);
                    jarOutStream.write(strategyConfig.getBytes("UTF8"));
                    continue;
                }
                if (name.startsWith("lastSettings.xml") && lastSettings != null) {
                    entry = new JarEntry("lastSettings.xml");
                    ((JarOutputStream)jarOutStream).putNextEntry(entry);
                    jarOutStream.write(lastSettings.getBytes("UTF8"));
                    continue;
                }
                ((JarOutputStream)jarOutStream).putNextEntry(zipEntry);
                while ((bufferSize = zip.read(buffer)) > 0) {
                    jarOutStream.write(buffer, 0, bufferSize);
                }
            }
        }
        response.put("filePath", (Object)filePath);
        try {
            response.put("newStrategyName", (Object)SQUtils.stripExtension((String)new File(filePath).getName()));
        }
        catch (Exception e) {
            Log.error("Error while saving file. ", (Throwable)e);
        }
        AlgoWizardRecentFiles.save(filePath);
        response.put("recentFiles", (Object)AlgoWizardRecentFiles.listJSON());
        response.put("success", (Object)L.t((String)"File saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onRefreshResources(Map<String, String[]> parameterMap) {
        try {
            String lastSettings = this.tryGetParam(parameterMap, "lastSettings")[0];
            String refreshed = this.addResources(lastSettings);
            if (refreshed == null) {
                return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Missing 'lastSettings'.", (Object[])new Object[0]), null);
            }
            JSONObject response = new JSONObject();
            response.put("lastSettings", (Object)refreshed);
            response.put("success", (Object)L.t((String)"Resources refreshed.", (Object[])new Object[0]));
            return response.toString();
        }
        catch (Exception e) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Refreshing resources failed.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String addResources(String lastSettings) {
        if (lastSettings == null) {
            return null;
        }
        try {
            Element settings = XMLUtil.stringToElement((String)lastSettings);
            ProjectResources.addDataResources((Element)settings);
            return XMLUtil.elementToString((Element)settings);
        }
        catch (Exception e) {
            Log.error("Adding resources failed", (Throwable)e);
            return lastSettings;
        }
    }

    private String onSaveToRetester(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String strategyConfig = this.tryGetParam(parameterMap, "strategyConfig")[0];
            String strategyName = null;
            String lastSettings = null;
            try {
                strategyName = this.tryGetParam(parameterMap, "strategyName")[0];
            }
            catch (Exception e) {
                strategyName = "AlgoWizardStrategy";
            }
            try {
                lastSettings = this.tryGetParam(parameterMap, "lastSettings")[0];
            }
            catch (Exception e) {
                // empty catch block
            }
            boolean isBacktested = false;
            try {
                isBacktested = Boolean.parseBoolean(this.tryGetParam(parameterMap, "backtested")[0]);
            }
            catch (Exception exception) {
                // empty catch block
            }
            try {
                if (isBacktested && this.backtester instanceof SQBacktester) {
                    String backtestID = this.tryGetParam(parameterMap, "backtestID")[0];
                    SQBacktester.getResultsGroup((String)backtestID);
                }
            }
            catch (Exception e) {
                isBacktested = false;
            }
            ResultsGroup rg = null;
            if (isBacktested && this.backtester instanceof SQBacktester) {
                String backtestID = this.tryGetParam(parameterMap, "backtestID")[0];
                rg = SQBacktester.getResultsGroup((String)backtestID).clone();
                rg.setName(strategyName);
            } else {
                rg = new ResultsGroup(strategyName);
                rg.addSubresult(strategyName, new SettingsMap());
                rg.setLastSettings(lastSettings);
                rg.computeAllStats();
                rg.portfolio().addStrategyXml(XMLUtil.stringToElement((String)strategyConfig));
            }
            SQProject retester = ProjectEngine.get((String)"Retester");
            retester.getResultsDatabank().add(rg, true);
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Strategy saved to Retester.", (Object[])new Object[0]));
        return response.toString();
    }

    private String chooseFilePath(String defaultFolder, String fileName) throws Exception {
        throw new Exception("Not implemented for Electron.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetBacktestResults(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        ResultsGroup rg = null;
        try {
            if (this.backtester instanceof SQBacktester) {
                String backtestID = this.tryGetParam(parameterMap, "backtestID")[0];
                rg = SQBacktester.getResultsGroup((String)backtestID);
            } else {
                rg = this.rgProvider.get(parameterMap, "AlgoWizardServlet");
            }
            Element elSettings = XMLUtil.stringToElement((String)rg.getLastSettings());
            Element elData = elSettings.getChild("Data");
            ChartSetups chartSetups = ProjectConfigHelper.getChartSetups((Element)elData);
            ChartSetup mainSetup = chartSetups.getMainSetup();
            ChartDef mainChart = mainSetup.getMainChart();
            String backtestSymbol = mainSetup.getSymbol();
            String backtestTimeframe = mainSetup.getTimeframe();
            String backtestDateRange = SQTime.toUIDateString((long)mainChart.getHistoryFrom()) + " - " + SQTime.toUIDateString((long)mainChart.getHistoryTo());
            String engine = Engines.getEngineName((int)mainSetup.getBacktestEngine());
            String precision = Precisions.toString((int)mainSetup.getTestPrecision());
            JSONObject info = new JSONObject();
            info.put("data", (Object)(backtestSymbol + " / " + backtestTimeframe + ", " + backtestDateRange));
            info.put("engine", (Object)engine);
            info.put("precision", (Object)precision);
            response.put("info", (Object)info);
            BestResultOverview resultOverview = new BestResultOverview();
            String text = resultOverview.print(rg, (byte)127);
            text = text.substring(text.indexOf("<body"));
            text = text.substring(0, text.indexOf("</body>") + 7);
            response.put("stats", (Object)text);
            OverviewTemplate template = (OverviewTemplate)OverviewTemplates.getInstance().findClassByName("SQDefaultPct");
            text = template.drawValues(rg, rg.getMainResultKey(), new StatsTypeCombination(0, 10, 127));
            String monthlyPerfTable = text.substring(text.indexOf("<div class=\"performance\">"));
            monthlyPerfTable = monthlyPerfTable.substring(0, monthlyPerfTable.indexOf("</div>") + 6);
            response.put("monthlyPerfPct", (Object)monthlyPerfTable);
        }
        catch (Exception ex) {
            String string = AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving failed.", (Object[])new Object[0]), (Throwable)ex);
            return string;
        }
        finally {
            if (rg != null) {
                rg.releaseLock("AlgoWizardServlet");
            }
        }
        response.put("success", (Object)L.t((String)"Backtest results loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onBacktest(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        Log.info("Incoming backtest request");
        try {
            int engine;
            String userID;
            String sessionName;
            Element elSettings;
            String brokerSymbols;
            String webSocketID;
            boolean doSimpleBacktest;
            boolean doNegation;
            boolean doBacktest;
            String strategyXML;
            String strategyName;
            block55: {
                strategyName = this.tryGetParam(parameterMap, "strategyName")[0];
                strategyXML = this.tryGetParam(parameterMap, "strategyXML")[0];
                String settingsXML = this.tryGetParam(parameterMap, "settings")[0];
                strategyXML = strategyXML.replace("&", "&#38;");
                settingsXML = settingsXML.replace("&", "&#38;");
                strategyXML = strategyXML.replace("___", " ");
                settingsXML = settingsXML.replace("___", " ");
                doBacktest = false;
                doNegation = false;
                doSimpleBacktest = false;
                webSocketID = "NONE";
                try {
                    doBacktest = Boolean.parseBoolean(this.tryGetParam(parameterMap, "doBacktest")[0]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    doNegation = Boolean.parseBoolean(this.tryGetParam(parameterMap, "doNegation")[0]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    doSimpleBacktest = Boolean.parseBoolean(this.tryGetParam(parameterMap, "doSimpleBacktest")[0]);
                }
                catch (Exception exception) {
                    // empty catch block
                }
                try {
                    webSocketID = this.tryGetParam(parameterMap, "webSocketID")[0];
                }
                catch (Exception exception) {
                    // empty catch block
                }
                brokerSymbols = this.getParam(parameterMap, "brokerSymbols", null);
                if (brokerSymbols != null && brokerSymbols.trim().isEmpty()) {
                    brokerSymbols = null;
                }
                elSettings = XMLUtil.stringToElement((String)settingsXML);
                sessionName = "No Session";
                if (isBacktestNode) {
                    try {
                        String sessionString = this.getParam(parameterMap, "session", null);
                        userID = this.getParam(parameterMap, "userID", null);
                        Log.debug("Checking session...");
                        if (sessionString == null || userID == null) break block55;
                        Element elSession = XMLUtil.stringToElement((String)sessionString);
                        sessionName = elSession.getAttributeValue("name");
                        Log.debug("Session: " + sessionName);
                        if (sessionName.equals("No Session")) break block55;
                        sessionName = userID + "_" + sessionName;
                        elSession.setAttribute("name", sessionName);
                        Session sessionLoaded = new Session();
                        sessionLoaded.setFromXML(elSession);
                        Session sessionNode = SessionManager.getSession((String)sessionName);
                        if (sessionNode == null) {
                            SessionManager.addSession((Session)sessionLoaded);
                            Log.debug("Session added to SessionManager: " + sessionLoaded.getSessionName());
                        } else if (!sessionLoaded.toText().equals(sessionNode.toText())) {
                            SessionManager.updateSession((Session)sessionLoaded);
                            Log.debug("Session updated in SessionManager: " + sessionLoaded.getSessionName());
                        } else {
                            Log.debug("Session definition already exists in SessionManager: " + sessionLoaded.getSessionName());
                        }
                        Element elOptions = elSettings.getChild("Options").getChild("BuildTradingOptions");
                        Element paramsEl = XMLUtil.tryAddElement((Element)elOptions, (String)"Params");
                        List paramElems = paramsEl.getChildren("Param");
                        for (int i = 0; i < paramElems.size(); ++i) {
                            Element paramElem = (Element)paramElems.get(i);
                            try {
                                String className = paramElem.getAttributeValue("className");
                                if (!className.equals("SessionOption")) continue;
                                paramElem.setText(sessionName);
                                Log.debug("Session option changed in settingsXML successfully");
                                break;
                            }
                            catch (Exception e) {
                                Log.error("Exc.", (Throwable)e);
                            }
                        }
                    }
                    catch (Exception e) {
                        throw new Exception("Failed to load Session data. " + e.getMessage(), e);
                    }
                }
            }
            if (isBacktestNode && strategyXML != null && strategyXML.contains("key=\"CBlock_")) {
                throw new Exception("Custom blocks are not supported yet in online version");
            }
            String backtestID = parameterMap.containsKey("backtestID") ? this.tryGetParam(parameterMap, "backtestID")[0] : UUID.randomUUID().toString();
            userID = null;
            if (parameterMap.containsKey("userID")) {
                userID = this.tryGetParam(parameterMap, "userID")[0];
            }
            String accountID = null;
            if (parameterMap.containsKey("accountID")) {
                accountID = this.tryGetParam(parameterMap, "accountID")[0];
            }
            String userSecretCode = null;
            if (parameterMap.containsKey("userSecretCode")) {
                userSecretCode = this.tryGetParam(parameterMap, "userSecretCode")[0];
            }
            double minDistance = 0.0;
            if (doNegation) {
                try {
                    strategyXML = this.negateSignals(strategyXML);
                    response.put("negatedXML", (Object)strategyXML);
                }
                catch (Exception e) {
                    Log.error("Negation error - ", (Throwable)e);
                    response.put("negationError", (Object)e.getMessage());
                    response.put("negatedXML", (Object)strategyXML);
                }
            }
            if ((engine = this.getEngine(elSettings)) == 1316847364) {
                String symbol = this.getMainSymbol(elSettings);
                String groupSymbols = this.getParam(parameterMap, "groupSymbols", null);
                this.checkStockpickerData(symbol, engine, userID, groupSymbols, elSettings);
            }
            if (doBacktest) {
                String mmEngine;
                Element elSetup;
                ChartSetups chartSetups = null;
                TradingOptions tradingOptions = null;
                MoneyManagementMethod mmMethod = null;
                RiskManagementMethod rmMethod = null;
                CommissionsMethod commission = CommissionsMethodsList.create((String)"None", (Object[])new Object[0]);
                SwapMethod swap = new SwapMethod();
                ATM atm = null;
                if (!isBacktestNode && Engines.hasSessionOption((int)engine)) {
                    sessionName = ProjectResources.getSession((Element)elSettings);
                }
                double slippage = 0.0;
                Element elData = elSettings.getChild("Data");
                try {
                    if (!sessionName.equals("No Session")) {
                        Element elSetups = elData.getChild("Setups");
                        List setups = elSetups.getChildren("Setup");
                        for (int a = 0; a < setups.size(); ++a) {
                            Element elChartSetup = (Element)setups.get(a);
                            elChartSetup.setAttribute("session", sessionName);
                        }
                    }
                    chartSetups = ProjectConfigHelper.getChartSetups((Element)elData);
                }
                catch (Exception e) {
                    throw new Exception("Unable to load backtest charts - " + e.getMessage(), e);
                }
                engine = chartSetups.getMainSetup().getBacktestEngine();
                for (int i = 0; i < chartSetups.size(); ++i) {
                    ChartSetup setup = (ChartSetup)chartSetups.get(i);
                    ArrayList charts = setup.getCharts();
                    for (int j = 0; j < charts.size(); ++j) {
                        ChartDef chart = (ChartDef)charts.get(j);
                        String symbol = chart.getSymbol();
                        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
                        if (dataInfo == null) {
                            throw new Exception(L.t((String)"Symbol with name '%s' doesn't exist.", (Object[])new Object[]{symbol}));
                        }
                        if (dataInfo.rows != 0 && dataInfo.dateFrom != 0L && dataInfo.dateTo != 0L) continue;
                        throw new Exception(L.t((String)"No data available for symbol '%s'.", (Object[])new Object[]{symbol}));
                    }
                }
                Element elStrategy = strategyXML.contains("Position Score") ? StrategyFixer.fixStrategy((String)strategyXML) : XMLUtil.stringToElement((String)strategyXML);
                VolumeProfileBlocks.checkStrategyAllowed((Element)elStrategy, (String)strategyName);
                CotSymbolResolver.resolve((Element)elStrategy, (String)chartSetups.getMainSetup().getSymbol());
                if (!StrategyChecker.strategyValid((Element)elStrategy) && engine != 1316847364 && engine != -1816889229) {
                    response.put("error", (Object)"Strategy doesn't contain any Rule or order open block");
                    return response.toString();
                }
                Element elRiskMoneyManagement = elSettings.getChild("RiskMoneyManagement");
                rmMethod = ProjectConfigHelper.getRiskManagement((Element)elRiskMoneyManagement.getChild("RiskManagement"));
                mmMethod = ProjectConfigHelper.getMoneyManagement((Element)elRiskMoneyManagement.getChild("MoneyManagement"));
                double initialCapital = mmMethod.getInitialCapital();
                tradingOptions = ProjectConfigHelper.getOptions((Element)elSettings.getChild("Options").getChild("BuildTradingOptions"));
                try {
                    elSetup = elData.getChild("Setups").getChild("Setup");
                    commission = ProjectConfigHelper.getCommissionsMethod((Element)elSetup);
                }
                catch (Exception e) {
                    throw new Exception("Cannot get commissions method", e);
                }
                try {
                    elSetup = elData.getChild("Setups").getChild("Setup");
                    swap = ProjectConfigHelper.getSwapMethod((Element)elSetup);
                }
                catch (Exception e) {
                    throw new Exception("Cannot get swap method", e);
                }
                try {
                    slippage = Double.parseDouble((String)ProjectConfigHelper.getChartSetupValues((Element)elData, (String)"slippage").get(0));
                }
                catch (Exception e) {
                    throw new Exception("Cannot get slippage value", e);
                }
                try {
                    minDistance = Double.parseDouble((String)ProjectConfigHelper.getChartSetupValues((Element)elData, (String)"minDist").get(0));
                }
                catch (Exception e) {
                    throw new Exception("Cannot get min distance value", e);
                }
                Element elATMs = elSettings.getChild("ATMs");
                if (elATMs != null) {
                    atm = new ATM(elATMs);
                    ATMConfigVerifier.verifyConfig((Element)elSettings);
                }
                if (doSimpleBacktest) {
                    for (int i = 0; i < chartSetups.size(); ++i) {
                        ChartSetup setup = (ChartSetup)chartSetups.get(i);
                        setup.setTestPrecision(1);
                        setup.setMinDistance(0.0);
                        ArrayList charts = setup.getCharts();
                        for (int a = 0; a < charts.size(); ++a) {
                            ChartDef chart = (ChartDef)charts.get(a);
                            String symbol = chart.getSymbol();
                            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
                            if (dataInfo == null || dataInfo.rows <= 0) continue;
                            long historyFrom = dataInfo.dateTo - 31536000000L;
                            if (engine == 1316847364) {
                                historyFrom = SQTime.addYears((long)dataInfo.dateTo, (int)-5);
                            }
                            long historyTo = dataInfo.dateTo;
                            chart.setHistoryFrom(historyFrom < dataInfo.dateFrom ? dataInfo.dateFrom : historyFrom);
                            chart.setHistoryTo(historyTo);
                        }
                    }
                }
                ChartSetup setup = (ChartSetup)chartSetups.get(0);
                long df = setup.getMainChart().getHistoryFrom();
                long dt = setup.getMainChart().getHistoryTo();
                if (df < 0L || dt < 0L) {
                    throw new Exception("Invalid history settings. Date from or Date to is smaller than 0.");
                }
                if (dt <= df) {
                    throw new Exception(L.t((String)"Date to %s must be greater than Date from %s.", (Object[])new Object[]{SQTime.toDateString((long)df), SQTime.toDateString((long)dt)}));
                }
                Log.info(String.format("Running %s backtest for %s/%s, from %s to %s", doSimpleBacktest ? "simple " : "full", setup.getSymbol(), setup.getTimeframe(), SQTime.toDateString((long)df), SQTime.toDateString((long)dt)));
                if (!(engine != 1316847364 && engine != -1816889229 || (mmEngine = mmMethod.getEngine()).equals("SP,SA"))) {
                    throw new Exception(L.t((String)"The specified MM method %s is not supported by Stockpicker engine.", (Object[])new Object[]{mmMethod.printFormatedName(), SQTime.toDateString((long)dt)}));
                }
                HashMap<String, Object> settings = new HashMap<String, Object>();
                settings.put("StrategyName", strategyName);
                settings.put("StrategyXml", elStrategy);
                settings.put("StrategyObject", StrategyBase.createXmlStrategy((Element)elStrategy, (String)strategyName));
                settings.put("ChartSetups", chartSetups);
                settings.put("MinDistance", minDistance);
                settings.put("Slippage", slippage);
                settings.put("Commission", commission);
                settings.put("Swap", swap);
                settings.put("MoneyManagement.InitialCapital", initialCapital);
                settings.put("MoneyManagement.Method", mmMethod);
                settings.put("RiskManagement", rmMethod);
                settings.put("FitnessFunction", this.getFitnessFunction());
                settings.put("TradingOptions", tradingOptions);
                settings.put("OutOfSample", new OutOfSample());
                settings.put("StrategyLastSettings", elSettings);
                settings.put("UserID", userID);
                settings.put("AccountID", accountID);
                settings.put("SimpleBacktest", doSimpleBacktest);
                settings.put("UserSecretCode", userSecretCode);
                settings.put("ATM", atm);
                settings.put("IsAlgoWizard", true);
                settings.put("BrokerSymbols", brokerSymbols);
                settings.put("webSocketID", webSocketID);
                this.backtester.run(backtestID, chartSetups.getMainSetup(), settings);
                response.put("backtestID", (Object)backtestID);
                response.put("backtestDateFrom", (Object)SQTime.toUIDateString((long)df));
                response.put("backtestDateTo", (Object)SQTime.toUIDateString((long)dt));
            }
            response.put("strategyXML", (Object)strategyXML);
            response.put("success", (Object)L.t((String)"Backtest started.", (Object[])new Object[0]));
        }
        catch (Exception ex) {
            Log.error("Backtest failed", (Throwable)ex);
            response.put("error", (Object)("Backtest failed - " + ex.getMessage()));
        }
        return response.toString();
    }

    private void checkStockpickerData(String symbol, int engine, String userID, String groupSymbols, Element elSettings) throws Exception {
        boolean isCustomGroup;
        if (engine != 1316847364) {
            return;
        }
        String originalSymbol = symbol;
        String basketName = null;
        boolean updateXml = false;
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
        if (dataInfo != null) {
            Log.info(String.format("Symbol found, symbol=%s, basketId=%d, available data from %s to %s", dataInfo.symbol, dataInfo.basketId, SQTime.toDateString((long)dataInfo.dateFrom), SQTime.toDateString((long)dataInfo.dateTo)));
        }
        if (dataInfo != null && dataInfo.basketId >= 0) {
            return;
        }
        boolean bl = isCustomGroup = groupSymbols != null && !groupSymbols.trim().isEmpty();
        if (isCustomGroup) {
            Log.info(String.format("Stockpicker custom group definition, symbol=%s, userID=%s, groupSymbols=%s", symbol, userID, groupSymbols));
            if (userID == null || userID.trim().isEmpty()) {
                throw new Exception("Custom group definition - userID cannot be null.");
            }
            symbol = symbol.replace("[", "").replace("]", "");
            basketName = "[" + symbol + "_" + userID + "]";
            int basketId = Math.abs((basketName + groupSymbols).hashCode()) * -1;
            BasketDto basket = BasketOfStocksManager.getInstance().getBasket(Integer.valueOf(basketId));
            if (basket == null) {
                BasketOfStocksManager.getInstance().createCustomGroup(basketName, basketId, groupSymbols, false, userID);
            }
            if ((dataInfo = DataManager.getDataInfo((String)"History", (String)basketName)) == null) {
                dataInfo = DataManager.addCustomData((String)"History", (String)basketName, (int)basketId, (String)originalSymbol);
            }
            dataInfo.basketId = basketId;
            Log.info(String.format("Stockpicker - custom group created %d", basketId));
            updateXml = true;
        } else if (dataInfo == null) {
            throw new DataException(2, L.t((String)"Group with name %s doesn't exist", (Object[])new Object[]{symbol}));
        }
        if (updateXml) {
            Log.info(String.format("Updating settings XML with newly created symbol for custom group: %s", basketName));
            List charts = elSettings.getChild("Data").getChild("Setups").getChild("Setup").getChildren("Chart");
            for (int i = 0; i < charts.size(); ++i) {
                Element elChart = (Element)charts.get(i);
                String chartSymbol = elChart.getAttributeValue("symbol");
                if (!chartSymbol.equals(originalSymbol) && !chartSymbol.equals("Same as main chart")) continue;
                elChart.setAttribute("symbol", basketName);
                Log.info(String.format("Updated chart %d symbol to %s", i, basketName));
            }
        }
    }

    private int getEngine(Element elSettings) throws Exception {
        try {
            Element elData = elSettings.getChild("Data");
            Element elSetup = elData.getChild("Setups").getChild("Setup");
            int engine = Engines.getEngine((String)elSetup.getAttributeValue("engine"));
            return engine;
        }
        catch (Exception e) {
            throw new Exception("Failed to parse engine.", e);
        }
    }

    private String getMainSymbol(Element elSettings) throws Exception {
        try {
            Element elData = elSettings.getChild("Data");
            Element elChart = elData.getChild("Setups").getChild("Setup").getChild("Chart");
            String symbol = elChart.getAttributeValue("symbol");
            if (symbol == null) {
                return null;
            }
            return XMLUtil.removeXMLCharacters((String)symbol);
        }
        catch (Exception e) {
            throw new Exception("Failed to parse main symbol.", e);
        }
    }

    private String onNegate(Map<String, String[]> parameterMap) {
        JSONObject response;
        block5: {
            response = new JSONObject();
            try {
                String strategyXML = this.tryGetParam(parameterMap, "strategyXML")[0];
                try {
                    if (this.isStandardStrategy(strategyXML)) {
                        response.put("strategyXML", (Object)this.negateSignals(strategyXML));
                        break block5;
                    }
                    response.put("strategyXML", (Object)this.negateStockpicker(strategyXML));
                }
                catch (Exception ex) {
                    Log.error("Cannot perform negation", (Throwable)ex);
                    response.put("strategyXML", (Object)strategyXML);
                    response.put("negationError", (Object)ex.getMessage());
                }
            }
            catch (Exception e) {
                Log.error("Cannot perform negation", (Throwable)e);
                return AlgoWizardServlet.apiErrorJSON((String)"Can't perform negation", (Throwable)e);
            }
        }
        response.put("success", (Object)L.t((String)"Negation done.", (Object[])new Object[0]));
        return response.toString();
    }

    private boolean isStandardStrategy(String strategyXML) {
        return !strategyXML.contains("pickerEditor=\"true\"");
    }

    private String onNegateCustomBlock(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String strategyXML = "<StrategyFile><Strategy><Variables/></Strategy></StrategyFile>";
            String blockXML = "<signal>" + this.tryGetParam(parameterMap, "blockXML")[0] + "</signal>";
            StrategyWithVariables strategy = new StrategyWithVariables(XMLUtil.stringToElement((String)strategyXML));
            Element elBlockToNegate = XMLUtil.stringToElement((String)blockXML);
            Element elNegatedBlock = this.negateBlockFromSignal(elBlockToNegate, strategy);
            this.fixCustomParamVariables(elNegatedBlock);
            String negatedXml = XMLUtil.elementToString((Element)elNegatedBlock);
            response.put("negatedBlock", (Object)negatedXml);
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot perform signal negation.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Signal negated", (Object[])new Object[0]));
        return response.toString();
    }

    private void fixCustomParamVariables(Element elParent) {
        String varType = elParent.getAttributeValue("variableType");
        if (varType != null && varType.equals("CustomParam")) {
            elParent.setAttribute("customParam", "true");
            String varName = elParent.getText();
            if (varName.startsWith("#")) {
                elParent.setAttribute("value", varName);
            }
            elParent.removeAttribute("variable");
            elParent.removeAttribute("variableType");
        }
        List children = elParent.getChildren();
        for (int i = 0; i < children.size(); ++i) {
            this.fixCustomParamVariables((Element)children.get(i));
        }
    }

    private String negateSignals(String strategyXML) throws Exception {
        Element elLongExitSignal;
        Element elStrategy = XMLUtil.stringToElement((String)strategyXML);
        Element elSignalRule = this.getSignalRule(elStrategy);
        StrategyWithVariables strategy = new StrategyWithVariables(elStrategy);
        boolean somethingNegated = false;
        Element elLongEntrySignal = this.getSignal(elSignalRule, VAR_ID_LONG_ENTRY);
        if (elLongEntrySignal != null) {
            Element elShortEntrySignal = this.getSignal(elSignalRule, VAR_ID_SHORT_ENTRY);
            if (elShortEntrySignal == null) {
                throw new Exception("No short entry signal found!");
            }
            Element elNegatedBlock = this.negateBlockFromSignal(elLongEntrySignal, strategy);
            if (elNegatedBlock != null) {
                elShortEntrySignal.removeContent();
                elShortEntrySignal.addContent((Content)elNegatedBlock);
                somethingNegated = true;
            }
        }
        if ((elLongExitSignal = this.getSignal(elSignalRule, VAR_ID_LONG_EXIT)) != null) {
            Element elShortExitSignal = this.getSignal(elSignalRule, VAR_ID_SHORT_EXIT);
            if (elShortExitSignal == null) {
                throw new Exception("No short exit signal found!");
            }
            Element elNegatedBlock = this.negateBlockFromSignal(elLongExitSignal, strategy);
            if (elNegatedBlock != null) {
                elShortExitSignal.removeContent();
                elShortExitSignal.addContent((Content)elNegatedBlock);
                somethingNegated = true;
            }
        }
        if (somethingNegated) {
            strategyXML = XMLUtil.xmlToString((Element)elStrategy);
        }
        Element elLongEntryRuleThen = this.getEntryRuleThen(elStrategy, 1);
        Element elShortEntryRuleThen = this.getEntryRuleThen(elStrategy, 2);
        if (elLongEntryRuleThen != null && elShortEntryRuleThen != null) {
            Element elNegatedAction = this.negateActionBlock(elLongEntryRuleThen, strategy);
            elShortEntryRuleThen.removeChildren("Item");
            elShortEntryRuleThen.addContent((Content)elNegatedAction);
            somethingNegated = true;
        }
        if (somethingNegated) {
            strategyXML = XMLUtil.xmlToString((Element)elStrategy);
        }
        return strategyXML;
    }

    private String negateStockpicker(String strategyXML) throws Exception {
        Element elLongOrder;
        Element elShortExit;
        Element elLongExit;
        Element elStrategy = XMLUtil.stringToElement((String)strategyXML);
        StrategyWithVariables strategy = new StrategyWithVariables(elStrategy);
        boolean somethingNegated = false;
        Element elLongRule = this.getSPRule(elStrategy, "Long");
        if (elLongRule == null) {
            throw new Exception("Cannot find SP long rule!");
        }
        Element elShortRule = this.getSPRule(elStrategy, "Short");
        if (elShortRule == null) {
            throw new Exception("Cannot find SP short rule!");
        }
        Element elLongEntry = elLongRule.getChild("Entry");
        if (elLongEntry == null) {
            throw new Exception("No long entry signal found!");
        }
        Element elShortEntry = elShortRule.getChild("Entry");
        if (elShortEntry == null) {
            throw new Exception("No short entry signal found!");
        }
        Element elNegatedBlock = this.negateBlockFromSignal(elLongEntry, strategy);
        if (elNegatedBlock != null) {
            elShortEntry.removeContent();
            elShortEntry.addContent((Content)elNegatedBlock);
            somethingNegated = true;
        }
        if ((elLongExit = this.getSPExit(elLongRule)) != null && (elShortExit = this.getSPExit(elShortRule)) != null && (elNegatedBlock = this.negateBlockFromSignal(elLongExit, strategy)) != null) {
            elShortExit.removeContent();
            elShortExit.addContent((Content)elNegatedBlock);
            somethingNegated = true;
        }
        if ((elLongOrder = elLongRule.getChild("Order")) == null) {
            throw new Exception("No long order found!");
        }
        Element elShortOrder = elShortRule.getChild("Order");
        if (elShortOrder == null) {
            throw new Exception("No short order found!");
        }
        elNegatedBlock = this.negateActionBlock(elLongOrder, strategy);
        if (elNegatedBlock != null) {
            elShortOrder.removeContent();
            elShortOrder.addContent((Content)elNegatedBlock);
            somethingNegated = true;
        }
        if (somethingNegated) {
            strategyXML = XMLUtil.xmlToString((Element)elStrategy);
        }
        return strategyXML;
    }

    private Element getSPExit(Element elLongRule) {
        List exits = elLongRule.getChildren("Exit");
        if (exits.size() > 1) {
            return (Element)exits.get(1);
        }
        return null;
    }

    private Element getSPRule(Element elStrategy, String ruleName) throws Exception {
        List events = elStrategy.getChild("Strategy").getChild("Rules").getChild("Events").getChildren("Event");
        Element elEventOnBarUpdate = null;
        for (int i = 0; i < events.size(); ++i) {
            Element elEvent = (Element)events.get(i);
            if (!elEvent.getAttributeValue("key").equals("OnBarUpdate")) continue;
            elEventOnBarUpdate = elEvent;
            break;
        }
        if (elEventOnBarUpdate == null) {
            throw new Exception("No OnBarUpdate event found in strategy.");
        }
        List rules = elEventOnBarUpdate.getChildren("Rule");
        if (rules.size() == 0) {
            throw new Exception("No rules found in OnBarUpdate event.");
        }
        for (int i = 0; i < rules.size(); ++i) {
            Element elRule = (Element)rules.get(i);
            if (!elRule.getAttributeValue("type").equals("StockpickerEntryExit") || !elRule.getAttributeValue("name").equals(ruleName)) continue;
            return elRule;
        }
        return null;
    }

    private Element negateActionBlock(Element elThen, StrategyWithVariables strategy) throws Exception {
        Element elBlock = elThen.getChild("Item").clone();
        if (this.negatersList == null) {
            this.negatersList = Negaters.list();
        }
        IBlock block = Blocks.getBlockObject((String)elBlock.getAttributeValue("key"), (StrategyBase)strategy, (Element)elBlock);
        IBlock negatedBlock = this.negatersList.negate(block, (StrategyBase)strategy);
        Element elNegatedBlock = Blocks.generateBlockTreeXml((IBlock)negatedBlock);
        return elNegatedBlock;
    }

    private Element getSignalRule(Element elStrategy) throws Exception {
        Element elRule = elStrategy.getChild("Strategy").getChild("Rules").getChild("Events").getChild("Event").getChild("Rule");
        if (!elRule.getAttributeValue("type").equals("Signal") && !elRule.getAttributeValue("type").equals("SignalFuzzy")) {
            throw new Exception("Rule is not a signal rule!");
        }
        return elRule;
    }

    private Element getEntryRuleThen(Element elStrategy, int ruleIndex) throws Exception {
        List rules = elStrategy.getChild("Strategy").getChild("Rules").getChild("Events").getChild("Event").getChildren("Rule");
        if (rules.size() <= 1) {
            throw new Exception("There are not enough rules!");
        }
        Element elRule = (Element)rules.get(ruleIndex);
        if (!elRule.getAttributeValue("type").equals("IfThen")) {
            throw new Exception("Rule is not an If-Then rule!");
        }
        return elRule.getChild("Then");
    }

    private Element negateBlockFromSignal(Element elSignal, StrategyWithVariables strategy) throws Exception {
        List children = elSignal.getChildren();
        if (children.size() == 0) {
            Log.debug("No conditions defined");
            return null;
        }
        if (children.size() > 1) {
            throw new Exception("Signal has more than one child!");
        }
        Element elItem = (Element)children.get(0);
        Element elBlock = elItem.clone();
        if (this.negatersList == null) {
            this.negatersList = Negaters.list();
        }
        IBlock block = Blocks.getBlockObject((String)elBlock.getAttributeValue("key"), (StrategyBase)strategy, (Element)elBlock);
        IBlock negatedBlock = this.negatersList.negate(block, (StrategyBase)strategy);
        Element elNegatedBlock = Blocks.generateBlockTreeXml((IBlock)negatedBlock);
        return elNegatedBlock;
    }

    private Element getSignal(Element elRule, String signalKey) throws Exception {
        List children = elRule.getChild("signals").getChildren("signal");
        for (int i = 0; i < children.size(); ++i) {
            Element elSignal = (Element)children.get(i);
            if (!elSignal.getAttributeValue("variable").equals(signalKey)) continue;
            return elSignal;
        }
        return null;
    }

    private String onStopBacktest(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String backtestID = this.tryGetParam(args, "backtestID")[0];
            this.backtester.stop(backtestID);
        }
        catch (Exception ex) {
            response.put("error", (Object)ex.getMessage());
        }
        response.put("success", (Object)L.t((String)"Backtest stopped.", (Object[])new Object[0]));
        return response.toString();
    }

    private long getDateFrom(long symbolFrom, long symbolTo) {
        Calendar cal = Calendar.getInstance();
        cal.setTimeInMillis(symbolTo);
        cal.add(1, -2);
        long from = cal.getTimeInMillis();
        return symbolFrom < from ? from : symbolFrom;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onResolveCotSymbols(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        ResultsGroup rg = null;
        try {
            String strategyXML = this.tryGetParam(parameterMap, "strategyXML")[0];
            Element elStrategy = XMLUtil.stringToElement((String)strategyXML);
            if (CotSymbolResolver.hasPlaceholder((Element)elStrategy)) {
                try {
                    if (this.backtester instanceof SQBacktester && parameterMap.containsKey("backtestID")) {
                        rg = SQBacktester.getResultsGroup((String)this.tryGetParam(parameterMap, "backtestID")[0]);
                        CotSymbolResolver.resolveForExport((Element)elStrategy, (Element)rg.getStrategyXml(), null);
                    }
                }
                catch (Exception e) {
                    Log.debug("No backtest result for the strategy");
                }
                strategyXML = XMLUtil.elementToString((Element)elStrategy);
            }
            response.put("strategyXML", (Object)strategyXML);
        }
        catch (Exception ex) {
            String string = AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot resolve COT symbols.", (Object[])new Object[0]), (Throwable)ex);
            return string;
        }
        finally {
            if (rg != null) {
                rg.releaseLock("AlgoWizardServlet");
            }
        }
        response.put("success", (Object)"COT symbols resolved.");
        return response.toString();
    }

    private IFitnessFunction getFitnessFunction() throws Exception {
        String xmlConfig = "<Rankings><FitnessCriteria method=\"ComputeFromStrategyResult\"><Settings><Ranking type=\"NetProfit\" /></Settings></FitnessCriteria></Rankings>";
        return ProjectConfigHelper.getFitnessFunction((Element)XMLUtil.stringToElement((String)xmlConfig));
    }

    private String onAddNewTimeframe(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            TimeframeManager.addTimeframe((String)timeframe);
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getTimeframes(), (String[])new String[]{"SQUANT", "QDM"});
        }
        catch (Exception ex) {
            response.put("error", (Object)ex.getMessage());
        }
        response.put("success", (Object)L.t((String)"Timeframe added.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveBlock(Map<String, String[]> parameterMap) {
        JSONObject response = new JSONObject();
        try {
            String blockKey = this.tryGetParam(parameterMap, "blockKey")[0];
            String blockType = this.tryGetParam(parameterMap, "blockType")[0];
            String blockParams = this.tryGetParam(parameterMap, "blockParams")[0];
            AlgoWizardBlocksTagCloud.save(blockKey, blockType, blockParams);
            response.put("blocksTagCloud", (Object)AlgoWizardBlocksTagCloud.listJSON());
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Block saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadExample(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String fileName = this.tryGetParam(args, "fileName")[0];
            String wholePath = MainApp.getDataPath() + "internal/web/AlgoWizard/examples/" + fileName;
            IProgram loader = Program.get((String)"Loader");
            ResultsGroup resultsGroup = (ResultsGroup)loader.call("loadFile", new Object[]{wholePath});
            response.put("lastSettingsXML", (Object)resultsGroup.getLastSettings());
            response.put("sourceCode", (Object)XMLUtil.elementToString((Element)resultsGroup.getStrategyXml()));
            response.put("fileName", (Object)SQUtils.stripExtension((String)fileName));
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Cannot load example.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Example loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadBlockGroups(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String blockGroupsXML = XMLUtil.elementToString((Element)RandomGroups.getXml());
            response.put("blockGroupsXML", (Object)blockGroupsXML);
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Loading block groups failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Block groups loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveBlockGroups(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"blockGroupsXML"});
        JSONObject response = new JSONObject();
        try {
            String blockGroupsXML = this.tryGetParamValue(args, "blockGroupsXML");
            RandomGroups.save((String)blockGroupsXML);
            if (this.notifyAlgoWizard(args)) {
                SQWebSocketManager.addToDataQueue((DataToSend)new DataToSend("randomGroups", new JSONObject().put("blockGroupsXML", (Object)XMLUtil.elementToString((Element)RandomGroups.getXml()))), (String[])new String[]{"SQUANT", "AlgoWizard"});
            }
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving block groups failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Block groups saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadCustomBlocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            response.put("customBlocksXML", (Object)XMLUtil.elementToString((Element)CustomBlocks.get()));
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Loading custom blocks failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Custom blocks loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListBackupsBlockGroups(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            response.put("backups", (Object)RandomGroups.listBackupFiles());
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Loading backups failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Backups loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onListBackupsCustomBlocks(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            response.put("backups", (Object)CustomBlocks.listBackupFiles());
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Loading backups failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Backups loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onSaveCustomBlocks(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"customBlocksXML"});
        JSONObject response = new JSONObject();
        try {
            String customSignalsXML = this.tryGetParamValue(args, "customBlocksXML");
            CustomBlocks.save((Element)XMLUtil.stringToElement((String)customSignalsXML));
            if (this.notifyAlgoWizard(args)) {
                SQWebSocketManager.addToDataQueue((DataToSend)new DataToSend("customBlocks", new JSONObject().put("customBlocksXML", (Object)XMLUtil.elementToString((Element)CustomBlocks.get()))), (String[])new String[]{"SQUANT", "AlgoWizard"});
            }
        }
        catch (Exception ex) {
            return AlgoWizardServlet.apiErrorJSON((String)L.t((String)"Saving custom blocks failed.", (Object[])new Object[0]), (Throwable)ex);
        }
        response.put("success", (Object)L.t((String)"Custom blocks saved.", (Object[])new Object[0]));
        return response.toString();
    }

    private boolean notifyAlgoWizard(Map<String, String[]> args) {
        String[] value = args.get("notifyAlgoWizard");
        return value != null && value.length > 0 && Boolean.parseBoolean(value[0]);
    }
}

