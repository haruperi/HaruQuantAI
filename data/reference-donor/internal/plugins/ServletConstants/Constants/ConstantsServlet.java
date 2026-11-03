/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.data.imports.Separators
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.datalib.timezone.Timezones
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.lib.whitelabel.AbstractBroker
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.BadStrategyException
 *  com.strategyquant.tradinglib.CommissionsMethod
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.DatabankSyncTypes
 *  com.strategyquant.tradinglib.GCTypes
 *  com.strategyquant.tradinglib.PortfolioInitialBalanceTypes
 *  com.strategyquant.tradinglib.PrecachedRequest
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.SwapTypes
 *  com.strategyquant.tradinglib.TripleSwapOptions
 *  com.strategyquant.tradinglib.atm.ATMMoveSL2BETypes
 *  com.strategyquant.tradinglib.atm.ATMTypes
 *  com.strategyquant.tradinglib.atm.exits.ATMExitLevels
 *  com.strategyquant.tradinglib.atm.sizes.ATMSizes
 *  com.strategyquant.tradinglib.commissions.CommissionsMethodsList
 *  com.strategyquant.tradinglib.correlation.CorrelationTypes
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod
 *  com.strategyquant.tradinglib.databank.DatabankColumnTypes
 *  com.strategyquant.tradinglib.exception.StrategyProblem
 *  com.strategyquant.tradinglib.optimization.OptimizationConst
 *  com.strategyquant.tradinglib.performance.Performance
 *  com.strategyquant.tradinglib.plugindef.app.IAppPlugin
 *  com.strategyquant.tradinglib.project.ProjectConditions
 *  com.strategyquant.tradinglib.project.websocket.DataUpdateTypes
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.project.websocket.WebSocketConst
 *  com.strategyquant.tradinglib.simulator.Engines
 *  com.strategyquant.tradinglib.strategy.SimpleStrategyTypes
 *  com.strategyquant.tradinglib.task.settings.buildmode.GenerationTypes
 *  com.strategyquant.tradinglib.task.settings.buildmode.StopConditionTypes
 *  com.strategyquant.tradinglib.task.settings.buildtype.ImproveTypes
 *  com.strategyquant.tradinglib.task.settings.buildtype.StrategyArchitectures
 *  com.strategyquant.tradinglib.task.settings.buildtype.StrategyDirections
 *  com.strategyquant.tradinglib.task.settings.buildtype.StrategyTypes
 *  com.strategyquant.tradinglib.task.settings.partstoimprove.ImproveActionTypes
 *  com.strategyquant.tradinglib.tasks.HelpTexts
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Servlet.impl.Constants;

import com.strategyquant.datalib.data.imports.Separators;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.datalib.timezone.Timezones;
import com.strategyquant.lib.L;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.lib.whitelabel.AbstractBroker;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.CommissionsMethod;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.DatabankSyncTypes;
import com.strategyquant.tradinglib.GCTypes;
import com.strategyquant.tradinglib.PortfolioInitialBalanceTypes;
import com.strategyquant.tradinglib.PrecachedRequest;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.SwapTypes;
import com.strategyquant.tradinglib.TripleSwapOptions;
import com.strategyquant.tradinglib.atm.ATMMoveSL2BETypes;
import com.strategyquant.tradinglib.atm.ATMTypes;
import com.strategyquant.tradinglib.atm.exits.ATMExitLevels;
import com.strategyquant.tradinglib.atm.sizes.ATMSizes;
import com.strategyquant.tradinglib.commissions.CommissionsMethodsList;
import com.strategyquant.tradinglib.correlation.CorrelationTypes;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.crosscheck.WalkForwardCrossCheckMethod;
import com.strategyquant.tradinglib.databank.DatabankColumnTypes;
import com.strategyquant.tradinglib.exception.StrategyProblem;
import com.strategyquant.tradinglib.optimization.OptimizationConst;
import com.strategyquant.tradinglib.performance.Performance;
import com.strategyquant.tradinglib.plugindef.app.IAppPlugin;
import com.strategyquant.tradinglib.project.ProjectConditions;
import com.strategyquant.tradinglib.project.websocket.DataUpdateTypes;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.project.websocket.WebSocketConst;
import com.strategyquant.tradinglib.simulator.Engines;
import com.strategyquant.tradinglib.strategy.SimpleStrategyTypes;
import com.strategyquant.tradinglib.task.settings.buildmode.GenerationTypes;
import com.strategyquant.tradinglib.task.settings.buildmode.StopConditionTypes;
import com.strategyquant.tradinglib.task.settings.buildtype.ImproveTypes;
import com.strategyquant.tradinglib.task.settings.buildtype.StrategyArchitectures;
import com.strategyquant.tradinglib.task.settings.buildtype.StrategyDirections;
import com.strategyquant.tradinglib.task.settings.buildtype.StrategyTypes;
import com.strategyquant.tradinglib.task.settings.partstoimprove.ImproveActionTypes;
import com.strategyquant.tradinglib.tasks.HelpTexts;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConstantsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(ConstantsServlet.class);
    private static ConstantsServlet instance;
    private String getAllResponse = null;

    public ConstantsServlet() {
        instance = this;
    }

    public static ConstantsServlet getInstance() {
        return instance;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "getAll": {
                return this.onGetAll();
            }
            case "listCommissionMethods": {
                return this.onListCommissionMethods();
            }
        }
        return ConstantsServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onGetAll() {
        JSONObject response = new JSONObject();
        JSONObject constants = new JSONObject();
        JSONArray precisions = new JSONArray();
        JSONObject selectedTF = new JSONObject().put("name", (Object)"Selected timeframe only (fastest)").put("value", 1).put("minTF", (Object)"X");
        JSONObject baseTF = new JSONObject().put("name", (Object)"1 minute data tick simulation (slow)").put("value", 2).put("minTF", (Object)"M1");
        JSONObject customSpread = new JSONObject().put("name", (Object)"Real Tick - custom spread (slowest)").put("value", 3).put("minTF", (Object)"TICK");
        JSONObject realSpread = new JSONObject().put("name", (Object)"Real Tick - real spread (slowest)").put("value", 4).put("minTF", (Object)"TICK");
        precisions.put((Object)selectedTF).put((Object)baseTF).put((Object)customSpread).put((Object)realSpread);
        constants.put("precisions", (Object)precisions);
        JSONArray dataTypes = new JSONArray();
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Stock").put("value", 1));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Futures").put("value", 2));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Forex").put("value", 3));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"CFDs").put("value", 4));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"ETF").put("value", 5));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Index").put("value", 6));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Crypto").put("value", 7));
        dataTypes.put((Object)new JSONObject().put("name", (Object)"Bond").put("value", 8));
        constants.put("dataTypes", (Object)dataTypes);
        JSONObject dataSource = new JSONObject();
        dataSource.put("file", 1);
        dataSource.put("dukascopy", 2);
        dataSource.put("darwinex", 4);
        dataSource.put("sqequity", 5);
        dataSource.put("sqfutures", 6);
        dataSource.put("crypto", 7);
        dataSource.put("yahoo", 3);
        dataSource.put("mt5api", 8);
        constants.put("dataSource", (Object)dataSource);
        JSONArray dataSources = new JSONArray();
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_FILE).put("value", 1));
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_DUKASCOPY).put("value", 2));
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_Yahoo).put("value", 3));
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_DARWINEX).put("value", 4));
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_Cryptocurrency).put("value", 7));
        if (MainApp.checkProduct((String)"SQUANT")) {
            dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_SQEquityData).put("value", 5));
            dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_SQFuturesData).put("value", 6));
        }
        dataSources.put((Object)new JSONObject().put("name", (Object)DataSources.NAME_MT5_API).put("value", 8));
        constants.put("dataSources", (Object)dataSources);
        JSONObject dataRanges = new JSONObject().put("sinceLastDate", (Object)"sinceLastDate").put("lastYear", (Object)"lastYear").put("last6Months", (Object)"last6Months").put("allTime", (Object)"allTime");
        constants.put("dataRanges", (Object)dataRanges);
        JSONObject barDataTypes = new JSONObject();
        barDataTypes.put("startOfBar", 1);
        barDataTypes.put("endOfBar", 2);
        constants.put("barDataTypes", (Object)barDataTypes);
        JSONObject directions = new JSONObject();
        directions.put("both", 0);
        directions.put("long", 1);
        directions.put("short", -1);
        constants.put("directions", (Object)directions);
        JSONObject sampleTypes = new JSONObject();
        sampleTypes.put("full", 127);
        sampleTypes.put("in", 10);
        sampleTypes.put("ist", 11);
        sampleTypes.put("isv", 40);
        sampleTypes.put("isvEvery", 66);
        sampleTypes.put("isv1", 41);
        sampleTypes.put("isv2", 42);
        sampleTypes.put("isv3", 43);
        sampleTypes.put("isv4", 44);
        sampleTypes.put("isv5", 45);
        sampleTypes.put("isv6", 46);
        sampleTypes.put("isv7", 47);
        sampleTypes.put("isv8", 48);
        sampleTypes.put("isv9", 49);
        sampleTypes.put("isv10", 50);
        sampleTypes.put("out", 20);
        sampleTypes.put("oosEvery", 77);
        sampleTypes.put("oos1", 21);
        sampleTypes.put("oos2", 22);
        sampleTypes.put("oos3", 23);
        sampleTypes.put("oos4", 24);
        sampleTypes.put("oos5", 25);
        sampleTypes.put("oos6", 26);
        sampleTypes.put("oos7", 27);
        sampleTypes.put("oos8", 28);
        sampleTypes.put("oos9", 29);
        sampleTypes.put("oos10", 30);
        sampleTypes.put("notrade", 99);
        constants.put("sampleTypes", (Object)sampleTypes);
        JSONArray sampleTypeList = new JSONArray();
        sampleTypeList.put((Object)new JSONObject().put("value", 127).put("name", (Object)SampleTypes.typeToString((byte)127)));
        sampleTypeList.put((Object)new JSONObject().put("value", 10).put("name", (Object)SampleTypes.typeToString((byte)10)));
        sampleTypeList.put((Object)new JSONObject().put("value", 11).put("name", (Object)SampleTypes.typeToString((byte)11)));
        sampleTypeList.put((Object)new JSONObject().put("value", 40).put("name", (Object)SampleTypes.typeToString((byte)40)));
        sampleTypeList.put((Object)new JSONObject().put("value", 66).put("name", (Object)SampleTypes.typeToString((byte)66)));
        sampleTypeList.put((Object)new JSONObject().put("value", 41).put("name", (Object)SampleTypes.typeToString((byte)41)));
        sampleTypeList.put((Object)new JSONObject().put("value", 42).put("name", (Object)SampleTypes.typeToString((byte)42)));
        sampleTypeList.put((Object)new JSONObject().put("value", 43).put("name", (Object)SampleTypes.typeToString((byte)43)));
        sampleTypeList.put((Object)new JSONObject().put("value", 44).put("name", (Object)SampleTypes.typeToString((byte)44)));
        sampleTypeList.put((Object)new JSONObject().put("value", 45).put("name", (Object)SampleTypes.typeToString((byte)45)));
        sampleTypeList.put((Object)new JSONObject().put("value", 46).put("name", (Object)SampleTypes.typeToString((byte)46)));
        sampleTypeList.put((Object)new JSONObject().put("value", 47).put("name", (Object)SampleTypes.typeToString((byte)47)));
        sampleTypeList.put((Object)new JSONObject().put("value", 48).put("name", (Object)SampleTypes.typeToString((byte)48)));
        sampleTypeList.put((Object)new JSONObject().put("value", 49).put("name", (Object)SampleTypes.typeToString((byte)49)));
        sampleTypeList.put((Object)new JSONObject().put("value", 50).put("name", (Object)SampleTypes.typeToString((byte)50)));
        sampleTypeList.put((Object)new JSONObject().put("value", 20).put("name", (Object)SampleTypes.typeToString((byte)20)));
        sampleTypeList.put((Object)new JSONObject().put("value", 77).put("name", (Object)SampleTypes.typeToString((byte)77)));
        sampleTypeList.put((Object)new JSONObject().put("value", 21).put("name", (Object)SampleTypes.typeToString((byte)21)));
        sampleTypeList.put((Object)new JSONObject().put("value", 22).put("name", (Object)SampleTypes.typeToString((byte)22)));
        sampleTypeList.put((Object)new JSONObject().put("value", 23).put("name", (Object)SampleTypes.typeToString((byte)23)));
        sampleTypeList.put((Object)new JSONObject().put("value", 24).put("name", (Object)SampleTypes.typeToString((byte)24)));
        sampleTypeList.put((Object)new JSONObject().put("value", 25).put("name", (Object)SampleTypes.typeToString((byte)25)));
        sampleTypeList.put((Object)new JSONObject().put("value", 26).put("name", (Object)SampleTypes.typeToString((byte)26)));
        sampleTypeList.put((Object)new JSONObject().put("value", 27).put("name", (Object)SampleTypes.typeToString((byte)27)));
        sampleTypeList.put((Object)new JSONObject().put("value", 28).put("name", (Object)SampleTypes.typeToString((byte)28)));
        sampleTypeList.put((Object)new JSONObject().put("value", 29).put("name", (Object)SampleTypes.typeToString((byte)29)));
        sampleTypeList.put((Object)new JSONObject().put("value", 30).put("name", (Object)SampleTypes.typeToString((byte)30)));
        constants.put("sampleTypeList", (Object)sampleTypeList);
        JSONObject plTypes = new JSONObject();
        plTypes.put("money", 10);
        plTypes.put("percent", 20);
        plTypes.put("pips", 30);
        plTypes.put("ticks", 30);
        plTypes.put("openMoney", 40);
        plTypes.put("openPercent", 50);
        constants.put("plTypes", (Object)plTypes);
        JSONObject propGridTypes = new JSONObject();
        propGridTypes.put("int", 1);
        propGridTypes.put("double", 2);
        propGridTypes.put("str", 30);
        propGridTypes.put("boolean", 3);
        propGridTypes.put("date", 20);
        propGridTypes.put("time", 10);
        propGridTypes.put("intList", 4);
        propGridTypes.put("strList", 5);
        constants.put("propGridTypes", (Object)propGridTypes);
        JSONObject resultTypes = new JSONObject();
        resultTypes.put("main", (Object)"main");
        resultTypes.put("portfolio", (Object)"portfolio");
        constants.put("resultTypes", (Object)resultTypes);
        JSONArray resultTypesList = new JSONArray();
        resultTypesList.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Main data")).put("value", (Object)"main"));
        resultTypesList.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Portfolio")).put("value", (Object)"portfolio"));
        for (ICrossCheck plugin : SQPluginManager.getPlugins(ICrossCheck.class)) {
            resultTypesList.put((Object)new JSONObject().put("name", (Object)plugin.getName()).put("value", (Object)plugin.getSettingName()).put("crosscheck", true).put("title", (Object)plugin.getColumnTitleTemplate()).put("walkforward", WalkForwardCrossCheckMethod.class.isAssignableFrom(plugin.getClass()) && !plugin.getSettingName().equals("OptProfileSysParamPermutation")));
        }
        constants.put("resultTypesList", (Object)resultTypesList);
        JSONArray wfSubresultsList = new JSONArray();
        wfSubresultsList.put((Object)new JSONObject().put("name", (Object)"WF").put("value", 30));
        wfSubresultsList.put((Object)new JSONObject().put("name", (Object)"WF Stability of").put("value", 31));
        wfSubresultsList.put((Object)new JSONObject().put("name", (Object)"WF Score of").put("value", 32));
        wfSubresultsList.put((Object)new JSONObject().put("name", (Object)"WF Special - ").put("value", 33));
        constants.put("wfSubresultsList", (Object)wfSubresultsList);
        JSONObject runningStatuses = new JSONObject();
        runningStatuses.put("beforeStart", 0);
        runningStatuses.put("finished", 3);
        runningStatuses.put("paused", 2);
        runningStatuses.put("pausing", 5);
        runningStatuses.put("running", 1);
        runningStatuses.put("stopped", 4);
        runningStatuses.put("stopping", 6);
        runningStatuses.put("error", 50);
        runningStatuses.put("loading", 100);
        constants.put("runningStatuses", (Object)runningStatuses);
        JSONArray taskHelps = new JSONArray();
        for (String tabName : HelpTexts.getAll().keySet()) {
            JSONObject helpObj = new JSONObject();
            helpObj.put("tabName", (Object)tabName);
            helpObj.put("helpText", (Object)HelpTexts.get((String)tabName));
            taskHelps.put((Object)helpObj);
        }
        constants.put("helpTexts", (Object)taskHelps);
        constants.put("dataUpdateTypes", (Object)new DataUpdateTypes().toJSON());
        JSONArray timeframes = WSDataObjects.getTimeframes().getDataArray();
        constants.put("timeframes", (Object)timeframes);
        JSONObject timeframe = new JSONObject();
        timeframe.put("Intraday", (Object)"Intraday");
        timeframe.put("TICK", (Object)"TICK");
        timeframe.put("M1", (Object)"M1");
        timeframe.put("M5", (Object)"M5");
        timeframe.put("M15", (Object)"M15");
        timeframe.put("M30", (Object)"M30");
        timeframe.put("H1", (Object)"H1");
        timeframe.put("H4", (Object)"H4");
        timeframe.put("D1", (Object)"D1");
        timeframe.put("Weekly", (Object)"Weekly");
        timeframe.put("Monthly", (Object)"Monthly");
        constants.put("timeframe", (Object)timeframe);
        JSONArray dbProperties = new JSONArray();
        constants.put("databankProperties", (Object)dbProperties);
        JSONObject optimization = new JSONObject();
        constants.put("optimization", (Object)optimization);
        JSONObject optimizations = new JSONObject();
        optimizations.put("simple", 1);
        optimizations.put("sequential", 4);
        optimizations.put("walk_fo", 2);
        optimizations.put("walk_fm", 3);
        optimization.put("optimizations", (Object)optimizations);
        JSONObject sources = new JSONObject();
        sources.put("file", 1);
        sources.put("databank", 2);
        optimization.put("sources", (Object)sources);
        JSONObject periodTypes = new JSONObject();
        periodTypes.put("percent", 10);
        periodTypes.put("days", 20);
        periodTypes.put("bars", 30);
        optimization.put("periodTypes", (Object)periodTypes);
        JSONObject optimizationTypes = new JSONObject();
        optimizationTypes.put("floating", 15);
        optimizationTypes.put("fixed", 25);
        optimization.put("optimizationTypes", (Object)optimizationTypes);
        JSONObject wfTypes = new JSONObject();
        wfTypes.put(OptimizationConst.wfTypeToString((int)0), 0);
        wfTypes.put(OptimizationConst.wfTypeToString((int)1), 1);
        wfTypes.put(OptimizationConst.wfTypeToString((int)2), 2);
        optimization.put("wfTypes", (Object)wfTypes);
        JSONObject wfType = new JSONObject();
        wfType.put("WF_TYPE_SIMIS_SIMOOS", 0);
        wfType.put("WF_TYPE_SIMIS_EXACTOOS", 1);
        wfType.put("WF_TYPE_EXACTIS_EXACTOOS", 2);
        optimization.put("wfType", (Object)wfType);
        JSONObject simpleOptimizations = new JSONObject();
        simpleOptimizations.put("storeAll", 5);
        simpleOptimizations.put("storeBest", 10);
        optimization.put("simpleOptimizations", (Object)simpleOptimizations);
        constants.put("engines", (Object)Engines.toJSON());
        constants.put("engineTypes", (Object)Engines.list());
        constants.put("engineKeys", (Object)Engines.toJSONKeys());
        JSONObject gedatabanks = new JSONObject();
        gedatabanks.put("results", (Object)"Results");
        gedatabanks.put("initialPopulation", (Object)"Initial population");
        gedatabanks.put("lastGeneration", (Object)"Last generation");
        gedatabanks.put("strategiesToImprove", (Object)"Strategies to improve");
        gedatabanks.put("strategiesToOptimize", (Object)"Strategies to optimize");
        gedatabanks.put("existingPortfolio", (Object)"Existing portfolio");
        gedatabanks.put("simpleStrategies", (Object)"Simple strategies");
        constants.put("gedatabanks", (Object)gedatabanks);
        constants.put("taskConfigs", (Object)WSDataObjects.getTaskTemplates().getDataArray());
        JSONObject performance = new JSONObject();
        performance.put("options", (Object)Performance.getCoreUsageOptions());
        performance.put("cores", Performance.totalCores);
        String coreUsage = MainApp.settings().get("coreUsage", "-1");
        performance.put("coreUsage", (Object)(coreUsage.startsWith("X") ? "X" : coreUsage));
        performance.put("customCores", coreUsage.startsWith("X") ? coreUsage.replaceAll("\\D+", "") : Integer.valueOf(Performance.totalCores));
        constants.put("performance", (Object)performance);
        JSONObject global = new JSONObject();
        global.put("soundsoff", Boolean.parseBoolean(MainApp.settings().get("globalSoundsOff", "true")));
        global.put("showControlOrders", Boolean.parseBoolean(MainApp.settings().get("showControlOrders", "false")));
        global.put("headerCustomText", (Object)MainApp.settings().get("headerCustomText", ""));
        global.put("footerCustomText", (Object)MainApp.settings().get("footerCustomText", ""));
        global.put("autoUpdate", Boolean.parseBoolean(MainApp.settings().get("autoUpdate", "true")));
        global.put("computePipsMetrics", Boolean.parseBoolean(MainApp.settings().get("ComputePipsMetrics", "false")));
        global.put("computePctsMetrics", Boolean.parseBoolean(MainApp.settings().get("ComputePctsMetrics", "false")));
        global.put("computeSeparateMetrics", Boolean.parseBoolean(MainApp.settings().get("ComputeSeparateMetrics", "true")));
        global.put("defaultResultToDisplay", (Object)MainApp.settings().get("defaultResultToDisplay", "portfolio"));
        constants.put("global", (Object)global);
        constants.put("buildStrategyTypes", (Object)new StrategyTypes().toJSON());
        constants.put("buildImproveTypes", (Object)new ImproveTypes().toJSON());
        constants.put("buildStrategyDirections", (Object)new StrategyDirections().toJSON());
        constants.put("buildGenerationTypes", (Object)new GenerationTypes().toJSON());
        constants.put("buildStopConditionTypes", (Object)new StopConditionTypes().toJSON());
        constants.put("improveActionTypes", (Object)new ImproveActionTypes().toJSON());
        constants.put("strategyArchitectures", (Object)new StrategyArchitectures().toJSON());
        new DatabankColumnTypes();
        constants.put("databankColumnTypes", (Object)DatabankColumnTypes.toJSONObject());
        JSONObject columnValueTypes = new JSONObject();
        columnValueTypes.put("Decimal2", (Object)"Decimal2");
        columnValueTypes.put("Decimal2Pct", (Object)"Decimal2Pct");
        columnValueTypes.put("Decimal2Pips", (Object)"Decimal2Pips");
        columnValueTypes.put("Decimal2PL", (Object)"Decimal2PL");
        columnValueTypes.put("Decimal4", (Object)"Decimal4");
        columnValueTypes.put("Decimal5", (Object)"Decimal5");
        columnValueTypes.put("Integer", (Object)"Integer");
        columnValueTypes.put("Text", (Object)"Text");
        constants.put("columnValueTypes", (Object)columnValueTypes);
        constants.put("WSConst", (Object)new WebSocketConst().toJSON());
        JSONObject channels = new JSONObject();
        channels.put("progress", (Object)"progress-channel");
        channels.put("databanks", (Object)"databanks-channel");
        channels.put("engine", (Object)"engine-channel");
        channels.put("engineCharts", (Object)"engine-charts-channel");
        channels.put("log", (Object)"log-channel");
        channels.put("bestResults", (Object)"best-results-channel");
        constants.put("channels", (Object)channels);
        JSONArray strategyProblems = new JSONArray();
        for (Object problem : BadStrategyException.listProblems()) {
            strategyProblems.put((Object)new JSONObject().put("code", ((StrategyProblem)problem).code).put("shortInfo", (Object)((StrategyProblem)problem).shortInfo).put("longInfo", (Object)((StrategyProblem)problem).longInfo));
        }
        constants.put("strategyProblems", (Object)strategyProblems);
        constants.put("importFileSeparators", (Object)Separators.toJSON());
        constants.put("simpleStrategyTypes", (Object)new SimpleStrategyTypes().toJSON());
        JSONArray timezones = new JSONArray();
        try {
            for (Timezone timezone : Timezones.getTimezones()) {
                JSONObject timezoneObj = new JSONObject();
                timezoneObj.put("name", (Object)timezone.getName());
                timezoneObj.put("value", (Object)timezone.getId());
                timezones.put((Object)timezoneObj);
            }
        }
        catch (Exception e) {
            return ConstantsServlet.apiErrorJSON((String)L.t((String)"Cannot list timezones.", (Object[])new Object[0]), (Throwable)e);
        }
        constants.put("timezones", (Object)timezones);
        JSONObject databankChange = new JSONObject();
        databankChange.put("add", (Object)"add");
        databankChange.put("remove", (Object)"remove");
        databankChange.put("update", (Object)"update");
        databankChange.put("reset", (Object)"reset");
        constants.put("databankChange", (Object)databankChange);
        constants.put("benchmarkTimePerTick", Performance.benchmarkTimePerTick);
        JSONObject equityChart = new JSONObject();
        equityChart.put("portfolioOnly", (Object)"Portfolio only");
        equityChart.put("portfolioPartsOnly", (Object)"Portfolio parts only");
        constants.put("equityChart", (Object)equityChart);
        constants.put("databankSyncTypes", (Object)new DatabankSyncTypes().toJSON());
        JSONArray cleanIntervals = new JSONArray();
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"never")).put("value", 0));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 10 seconds")).put("value", 10000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 20 seconds")).put("value", 20000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 30 seconds")).put("value", 30000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 45 seconds")).put("value", 40000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every minute")).put("value", 60000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 2 minutes")).put("value", 120000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 5 minutes")).put("value", 300000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 10 minutes")).put("value", 600000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 15 minutes")).put("value", 900000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every 30 minutes")).put("value", 1800000));
        cleanIntervals.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"every hour")).put("value", 3600000));
        constants.put("memoryCleanupIntervals", (Object)cleanIntervals);
        JSONObject products = new JSONObject();
        products.put("SQ", (Object)"SQUANT");
        products.put("AW", (Object)"AlgoWizard");
        products.put("QDM", (Object)"QDM");
        constants.put("products", (Object)products);
        constants.put("gcTypes", (Object)new GCTypes().toJSON());
        AbstractBroker broker = MainApp.getLicenseInfo().getBroker();
        if (broker != null) {
            JSONArray platforms = new JSONArray();
            String[] sp = broker.getSupportedPlatforms();
            if (sp != null) {
                for (int i = 0; i < sp.length; ++i) {
                    platforms.put((Object)sp[i]);
                }
            }
            constants.put("broker", (Object)new JSONObject().put("name", (Object)broker.getName()).put("encryption", broker.usesEAEncryption()).put("platforms", (Object)platforms).put("bannerFileName", (Object)broker.getBannerFileName()).put("welcomeTitle", (Object)broker.getWelcomeTitle()).put("welcomeSubtitle", (Object)broker.getWelcomeSubtitle()).put("description", (Object)broker.getDescription()).put("firstTimeLabel", (Object)broker.getFirstTimeLabel()).put("startButtonTitle", (Object)broker.getStartButtonTitle()).put("startButtonSubtitle", (Object)broker.getStartButtonSubtitle()));
        }
        constants.put("projectConditionTypes", (Object)ProjectConditions.toJSON());
        JSONObject projectConditionFields = new JSONObject();
        projectConditionFields.put("comparator", (Object)"comparator");
        projectConditionFields.put("databank", (Object)"databank");
        projectConditionFields.put("duration", (Object)"duration");
        projectConditionFields.put("number", (Object)"number");
        constants.put("projectConditionFields", (Object)projectConditionFields);
        JSONObject customDataType = new JSONObject();
        customDataType.put("IndicatorValuePrice", 1);
        customDataType.put("IndicatorValueNumber", 2);
        customDataType.put("IndicatorValuePriceRange", 3);
        customDataType.put("SignalValueBoolean", 10);
        customDataType.put("SignalValueAction", 11);
        constants.put("customDataType", (Object)customDataType);
        JSONArray customDataTypes = new JSONArray();
        customDataTypes.put((Object)new JSONObject().put("name", (Object)"Indicator value - price").put("value", 1));
        customDataTypes.put((Object)new JSONObject().put("name", (Object)"Indicator value - number").put("value", 2));
        customDataTypes.put((Object)new JSONObject().put("name", (Object)"Indicator value - price range").put("value", 3));
        customDataTypes.put((Object)new JSONObject().put("name", (Object)"Signal - 0 means false, anything else means true").put("value", 10));
        constants.put("customDataTypes", (Object)customDataTypes);
        constants.put("portfolioInitialBalanceTypes", (Object)new PortfolioInitialBalanceTypes().toJSON());
        JSONObject projectResourceStatuses = new JSONObject();
        projectResourceStatuses.put("doesntExist", 0);
        projectResourceStatuses.put("differs", 1);
        projectResourceStatuses.put("notEnoughData", 2);
        projectResourceStatuses.put("existsWithDifferentName", 3);
        constants.put("projectResourceStatuses", (Object)projectResourceStatuses);
        JSONObject valueTypes = new JSONObject();
        valueTypes.put("maximize", 1);
        valueTypes.put("minimize", 2);
        valueTypes.put("aproximate", 3);
        constants.put("valueTypes", (Object)valueTypes);
        JSONObject projectResourceActionTypes = new JSONObject();
        projectResourceActionTypes.put("loadProject", 0);
        projectResourceActionTypes.put("loadTaskConfig", 1);
        projectResourceActionTypes.put("applyStrategyConfig", 2);
        projectResourceActionTypes.put("loadTemplate", 3);
        projectResourceActionTypes.put("loadStrategyToOptimize", 4);
        projectResourceActionTypes.put("resolveProjectResources", 5);
        constants.put("projectResourceActionTypes", (Object)projectResourceActionTypes);
        JSONObject defaultDatabankViews = new JSONObject();
        defaultDatabankViews.put("main", (Object)"Default - Main data");
        defaultDatabankViews.put("portfolio", (Object)"Default - Portfolio");
        constants.put("defaultDatabankViews", (Object)defaultDatabankViews);
        constants.put("atmTypes", (Object)new ATMTypes().toJSON());
        constants.put("atmPositionSizes", (Object)new ATMSizes().toJSON());
        constants.put("atmExitLevels", (Object)new ATMExitLevels().toJSON());
        constants.put("atmMoveSL2BETypes", (Object)new ATMMoveSL2BETypes().toJSON());
        JSONArray correlationTypes = new JSONArray();
        for (CorrelationType type : CorrelationTypes.getInstance().getAvailableClasses()) {
            JSONObject typeObj = new JSONObject();
            typeObj.put("name", (Object)type.getName());
            typeObj.put("value", (Object)type.getClass().getSimpleName());
            correlationTypes.put((Object)typeObj);
        }
        constants.put("correlationTypes", (Object)correlationTypes);
        JSONArray correlationPeriods = new JSONArray();
        correlationPeriods.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Hour")).put("value", 5));
        correlationPeriods.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Day")).put("value", 10));
        correlationPeriods.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Week")).put("value", 20));
        correlationPeriods.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Month")).put("value", 30));
        correlationPeriods.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"Year")).put("value", 40));
        constants.put("correlationPeriods", (Object)correlationPeriods);
        constants.put("swapTypes", (Object)new SwapTypes().toJSON());
        constants.put("tripleSwapOptions", (Object)new TripleSwapOptions().toJSON());
        constants.put("isBrazilianEdition", MainApp.isBrazilianEdition());
        constants.put("isProEdition", MainApp.getLicenseInfo().isProEdition());
        constants.put("AWEditorVersion", (Object)MainApp.settings().get("AWEditorVersion", "2"));
        constants.put("commissionMethods", (Object)this.getCommissionMethodsJSON());
        constants.put("isFirstRun", MainApp.isFirstRun());
        response.put("constants", (Object)constants);
        response.put("success", (Object)L.t((String)"Constants returned.", (Object[])new Object[0]));
        JSONArray pcSelectionTypes = new JSONArray();
        pcSelectionTypes.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"SharpeRatio")).put("value", (Object)"SharpRatio"));
        pcSelectionTypes.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"ReturnDrawdownRatio")).put("value", (Object)"ReturnDrawdownRatio"));
        pcSelectionTypes.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"CAGRMaxDrawdownRatio")).put("value", (Object)"CAGRMaxDrawdownRatio"));
        pcSelectionTypes.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"CAGRMeanDrawdownRatio")).put("value", (Object)"CAGRMeanDrawdownRatio"));
        pcSelectionTypes.put((Object)new JSONObject().put("name", (Object)L.tsq((String)"NetProfit")).put("value", (Object)"NetProfit"));
        constants.put("pcSelectionTypes", (Object)pcSelectionTypes);
        constants.put("useHttps", Boolean.parseBoolean(MainApp.settings().get("SSLUse", "false")));
        JSONArray appPlugins = new JSONArray();
        for (IAppPlugin plugin : SQPluginManager.getPlugins(IAppPlugin.class)) {
            appPlugins.put((Object)new JSONObject().put("name", (Object)plugin.getName()).put("appCode", (Object)plugin.getAppCode()).put("disabledForSpecialTrial", plugin.disabledForSpecialTrial()));
        }
        constants.put("appPlugins", (Object)appPlugins);
        constants.put("appPath", (Object)MainApp.getDataPath());
        return response.toString();
    }

    @PrecachedRequest(relativeURL="/constants/listCommissionMethods")
    private String onListCommissionMethods() {
        JSONObject response = new JSONObject();
        JSONArray methods = null;
        if (!MainApp.checkProduct((String)"QDM")) {
            try {
                methods = this.getCommissionMethodsJSON();
            }
            catch (Exception e) {
                return ConstantsServlet.apiErrorJSON((String)L.t((String)"Cannot get commission methods.", (Object[])new Object[0]), (Throwable)e);
            }
        } else {
            methods = new JSONArray();
        }
        response.put("methods", (Object)methods);
        response.put("success", (Object)L.t((String)"Commission methods listed.", (Object[])new Object[0]));
        return response.toString();
    }

    private JSONArray getCommissionMethodsJSON() {
        JSONArray methods = new JSONArray();
        for (CommissionsMethod method : CommissionsMethodsList.get().getAvailableClasses()) {
            JSONObject methodObj = new JSONObject();
            methodObj.put("name", (Object)method.getName());
            methodObj.put("help", (Object)method.getNote());
            methodObj.put("class", (Object)method.getClass().getSimpleName());
            methodObj.put("config", (Object)XMLUtil.elementToString((Element)method.getXML()));
            methodObj.put("display", (Object)method.getFormatedName());
            methods.put((Object)methodObj);
        }
        return methods;
    }
}

