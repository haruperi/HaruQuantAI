/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerator
 *  com.strategyquant.lib.sourcecode.SourceCodeGenerators
 *  com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.sourcecode.SourceCodeGenerator;
import com.strategyquant.lib.sourcecode.SourceCodeGenerators;
import com.strategyquant.lib.sourcecode.XMLIndicatorsAnalyzer;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.DatabankColumn;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.OverviewTemplate;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.databank.DatabankColumns;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.miniequitychart.MiniEquityChartComputer;
import com.strategyquant.tradinglib.project.StrategyXMLModifier;
import com.strategyquant.tradinglib.project.bestresults.BestResultOverview;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.overview.OverviewTemplates;
import com.strategyquant.tradinglib.strategy.DataItemsGenerator;
import java.util.HashMap;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ResultsPanelData {
    private static final Logger Log = LoggerFactory.getLogger(ResultsPanelData.class);

    public static void load(ResultsGroup resultsGroup, JSONObject jSONObject, JSONObject jSONObject2) throws Exception {
        OverviewTemplate overviewTemplate = (OverviewTemplate)OverviewTemplates.getInstance().findClassByName("SQDefaultWithPortfolio");
        String string = overviewTemplate.drawValues(resultsGroup, "Portfolio", new StatsTypeCombination(0, 10, 127));
        BestResultOverview bestResultOverview = new BestResultOverview();
        jSONObject.put("fullResult", (Object)"NA");
        jSONObject.put("result", (Object)bestResultOverview.print(resultsGroup, (byte)127));
        jSONObject2.put("product", (Object)"AlgoWizard");
        jSONObject2.put("projectName", (Object)"AlgoWizard");
        jSONObject2.put("databankName", (Object)"AlgoWizard");
        jSONObject2.put("strategyName", (Object)String.format("%s - %d", "AlgoWizard", System.currentTimeMillis()));
        jSONObject2.put("fileName", (Object)resultsGroup.getName());
        jSONObject2.put("taskType", (Object)"AlgoWizard");
        jSONObject2.put("taskName", (Object)"AlgoWizard");
        jSONObject2.put("isTaskManager", false);
        jSONObject2.put("isAlgoWizard", true);
        jSONObject2.put("resultInfo", (Object)"AlgoWizard");
        jSONObject2.put("isWFResult", false);
        jSONObject2.put("isPortfolio", resultsGroup.isPortfolio());
        DataItemsGenerator.get(jSONObject2, resultsGroup);
        JSONArray jSONArray = new JSONArray();
        for (String string2 : resultsGroup.getResultKeys()) {
            jSONArray.put((Object)string2);
        }
        jSONObject2.put("dataItems", (Object)jSONArray);
        jSONObject.put("resultsParams", (Object)jSONObject2);
        jSONObject.put("equityChart", (Object)new JSONObject(ResultsPanelData.getEquityData(resultsGroup)));
    }

    public static void loadAC(JSONObject jSONObject, String string, ResultsGroup resultsGroup) throws Exception {
        String string2 = null;
        try {
            string2 = MiniEquityChartComputer.getValue(resultsGroup, resultsGroup.getMainResultKey(), (byte)127);
        }
        catch (Throwable throwable) {
            Log.error("Cannot get mini equity chart value (backtestID: " + string + ")", throwable);
        }
        jSONObject.put("miniEquityChart", (Object)string2);
        try {
            Result result = resultsGroup.mainResult();
            jSONObject.put("symbol", result.get(SpecialValues.Symbol));
            jSONObject.put("timeframe", result.get(SpecialValues.Timeframe));
            JSONObject jSONObject2 = new JSONObject();
            String[] stringArray = new String[]{"NetProfit", "NumberOfTrades", "DrawdownPct", "SharpeRatio", "ProfitFactor", "AvgProfitPerDay"};
            for (int i = 0; i < stringArray.length; ++i) {
                String string3 = stringArray[i];
                String string4 = "N/A";
                try {
                    string4 = ((DatabankColumn)DatabankColumns.get().findClassByName(string3)).getValue(resultsGroup, resultsGroup.getMainResultKey(), (byte)0, (byte)10, (byte)127);
                }
                catch (Exception exception) {
                    Log.error("Cannot get value of " + string3, (Throwable)exception);
                }
                jSONObject2.put(string3, (Object)string4);
            }
            jSONObject.put("stats", (Object)jSONObject2);
        }
        catch (Throwable throwable) {
            Log.error("Cannot get strategy stats (backtestID: " + string + ")", throwable);
        }
    }

    public static void loadACExample(JSONObject jSONObject, String string, ResultsGroup resultsGroup) throws Exception {
        String string2 = resultsGroup.getLastSettings();
        jSONObject.put("strategyXML", (Object)XMLUtil.elementToString((Element)resultsGroup.getStrategyXml()));
        jSONObject.put("lastSettingsXML", (Object)string2);
        OverviewTemplate overviewTemplate = (OverviewTemplate)OverviewTemplates.getInstance().findClassByName("DefaultOpenDD");
        jSONObject.put("overviewHTML", (Object)overviewTemplate.drawValues(resultsGroup, resultsGroup.getMainResultKey(), new StatsTypeCombination(0, 10, 127)));
        Element element = StrategyXMLModifier.getUpdatedStrategyXML(resultsGroup, resultsGroup.getStrategyXml(), "fromStrategy", resultsGroup.getName(), string2, null);
        XMLIndicatorsAnalyzer.init();
        XMLIndicatorsAnalyzer.fixItemAttributes((Element)element);
        SourceCodeGenerator sourceCodeGenerator = SourceCodeGenerators.getInstance().getGeneratorFromName("Pseudo Code(*.TXT)");
        jSONObject.put("sourceCode", (Object)sourceCodeGenerator.getSource(resultsGroup.getName(), element, 1.0, 1.0));
    }

    public static String getEquityData(ResultsGroup resultsGroup) {
        EquityChart equityChart = new EquityChart();
        equityChart.reset();
        equityChart.setPLType((byte)10);
        equityChart.setDomainAxisType("trade");
        equityChart.zoom(true, 350, 0L, Long.MAX_VALUE);
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        try {
            OrdersList ordersList = resultsGroup.orders().filter("Portfolio", (byte)0, (byte)127, true);
            MainChartDataset mainChartDataset = EquityChartUtils.generateDataset(ordersList, "trade");
            mainChartDataset.title = "Balance";
            mainChartDataset.filled = true;
            mainChartDataset.fillColor = "#DAF5FF";
            mainChartDataset.fillNegativeColor = "#F49C9C";
            mainChartDataset.thickness = 1;
            equityChart.addMainChartDataset(mainChartDataset);
            for (IEquityChartAddon iEquityChartAddon : SQPluginManager.getPlugins(IEquityChartAddon.class)) {
                try {
                    if (iEquityChartAddon.getName() == null || !iEquityChartAddon.getName().equals("Drawdown")) continue;
                    HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
                    hashMap.put("drawdown", new String[]{"111"});
                    iEquityChartAddon.print(equityChart, resultsGroup, resultsGroup.getMainResultKey(), ordersList, hashMap, "trade");
                    break;
                }
                catch (Exception exception) {
                    Log.error("Error while rendering EquityChart addon '" + iEquityChartAddon.getName() + "'. Exc.", (Throwable)exception);
                }
            }
            equityChart.fillJSON(jsonCreator);
        }
        catch (Exception exception) {
            Log.error("Cannot create equity chart dataset", (Throwable)exception);
            jsonCreator.put("error", (Object)exception.getMessage(), false);
        }
        jsonCreator.endObject(false);
        return jsonCreator.toJson();
    }
}

