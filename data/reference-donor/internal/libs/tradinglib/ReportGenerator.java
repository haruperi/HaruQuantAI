/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.pluginlib.program.Program
 *  org.apache.commons.codec.binary.Base64
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.OverviewTemplate;
import com.strategyquant.tradinglib.PlTypes;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.StatsDontExistException;
import com.strategyquant.tradinglib.StatsTypeCombination;
import com.strategyquant.tradinglib.TradeAnalysisChart;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.strategy.DataItemsGenerator;
import com.strategyquant.tradinglib.tradeanalysis.TradeAnalysisChartsList;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Map;
import java.util.TreeMap;
import org.apache.commons.codec.binary.Base64;
import org.json.JSONArray;
import org.json.JSONObject;

public class ReportGenerator
extends OverviewTemplate {
    protected File file;
    private ResultsGroup strategyResult;
    private JSONArray chartsResolved;
    private DataToSend wsData;
    private Thread waitingThread;
    private volatile boolean resolved = false;
    private String format;

    public ReportGenerator(String string) {
        this.format = string;
        this.wsData = new DataToSend("GenerateCharts", new JSONObject().put("format", (Object)string));
    }

    @Override
    public String drawValues(ResultsGroup resultsGroup, String string, StatsTypeCombination statsTypeCombination) throws Exception {
        this.strategyResult = resultsGroup;
        this.reset();
        this.addInfo(resultsGroup, string);
        this.addErrorsTable(resultsGroup, string);
        this.generateCharts(resultsGroup, string);
        this.replaceValues(resultsGroup, string, statsTypeCombination);
        return this.print();
    }

    private void addInfo(ResultsGroup resultsGroup, String string) {
        String string2 = DataItemsGenerator.getResultInfo(resultsGroup);
        this.template = this.template.replace("${Strategy_Info}", string2);
    }

    private void generateCharts(ResultsGroup resultsGroup, String string) throws Exception {
        this.chartsResolved = null;
        HashMap<String, String[]> hashMap = new HashMap<String, String[]>();
        hashMap.put("projectName", new String[]{resultsGroup.getDatabank().getProject()});
        hashMap.put("resultKey", new String[]{"Portfolio"});
        hashMap.put("databankName", new String[]{resultsGroup.getDatabank().getName()});
        hashMap.put("strategyName", new String[]{resultsGroup.getName()});
        hashMap.put("sampleType", new String[]{"127"});
        hashMap.put("direction", new String[]{"0"});
        hashMap.put("dailychart", new String[]{"false"});
        hashMap.put("drawdown", new String[]{"10"});
        hashMap.put("equity", new String[]{"off"});
        hashMap.put("height", new String[]{"619"});
        hashMap.put("history", new String[]{"false"});
        hashMap.put("points", new String[]{"off"});
        hashMap.put("stagnation", new String[]{"0"});
        hashMap.put("trendline", new String[]{"false"});
        hashMap.put("volatility", new String[]{"false"});
        hashMap.put("volume", new String[]{"5"});
        hashMap.put("width", new String[]{"1153"});
        hashMap.put("xaxis", new String[]{"time"});
        hashMap.put("yearmarker", new String[]{"true"});
        hashMap.put("zoom", new String[]{"false"});
        hashMap.put("zoommaxX", new String[]{"-1"});
        hashMap.put("zoomminX", new String[]{"-1"});
        hashMap.put("zoomwidth", new String[]{"-1"});
        hashMap.put("benchmarkActive", new String[]{"false"});
        hashMap.put("benchmarkSymbol", new String[]{"SPY.D"});
        hashMap.put("benchmarkNormalization", new String[]{"off"});
        JSONObject jSONObject = new JSONObject((String)Program.get((String)"ResultsEquityChart").call("printResultsGroup", new Object[]{resultsGroup, hashMap})).getJSONObject("chart");
        this.wsData.getDataObject().put("equityChart", (Object)jSONObject);
        hashMap.clear();
        hashMap.put("project", new String[]{resultsGroup.getDatabank().getProject()});
        hashMap.put("projectName", new String[]{resultsGroup.getDatabank().getProject()});
        hashMap.put("resultKey", new String[]{"Portfolio"});
        hashMap.put("databank", new String[]{resultsGroup.getDatabank().getName()});
        hashMap.put("databankName", new String[]{resultsGroup.getDatabank().getName()});
        hashMap.put("strategy", new String[]{resultsGroup.getName()});
        hashMap.put("strategyName", new String[]{resultsGroup.getName()});
        hashMap.put("sampleType", new String[]{"127"});
        hashMap.put("direction", new String[]{"0"});
        String string2 = "PLbyHourChart,PLbyWeekdayChart,TradesByWeekdayChart,LongShortProfitLossChart,WinLossCountByWeekdayChart,WinLossPLByMonthChart,LongShortTradesChart,PLGrowthByDurationChart,TradesByHourChart,PLLongChart,PLShortChart,TradesByDurationChart";
        hashMap.put("charts", new String[]{string2});
        hashMap.put("period", new String[]{"1"});
        hashMap.put("year", new String[]{"All"});
        JSONArray jSONArray = new JSONObject((String)Program.get((String)"ResultsTradeAnalysis").call("printResultsGroup", new Object[]{resultsGroup, hashMap})).getJSONArray("charts");
        this.wsData.getDataObject().put("charts", (Object)jSONArray);
        this.wsData.getDataObject().put("types", (Object)new JSONArray(Arrays.asList(string2.split(","))));
        SQWebSocketManager.addToDataQueue(this.wsData, "RESULTS");
        this.resolved = false;
        this.waitingThread = new Thread(){

            @Override
            public void run() {
                while (!ReportGenerator.this.resolved) {
                    try {
                        Thread.sleep(50L);
                    }
                    catch (Exception exception) {}
                }
            }
        };
        this.waitingThread.start();
        try {
            this.waitingThread.join(10000L);
        }
        catch (InterruptedException interruptedException) {
            Log.error("Waiting for confirmation interrupted.", (Throwable)interruptedException);
        }
        this.waitingThread = null;
        if (this.chartsResolved == null) {
            return;
        }
        int n = 1;
        for (int i = 0; i < this.chartsResolved.length(); ++i) {
            Object object;
            String string3;
            String string4;
            JSONObject jSONObject2 = this.chartsResolved.getJSONObject(i);
            String string5 = jSONObject2.getString("key");
            String string6 = jSONObject2.getString("img");
            string6 = string6.replaceAll("data:image/png;base64,", "");
            string6 = string6.replaceAll(" ", "+");
            if (string5.contains("equityChart")) {
                string4 = this.escapeChartName(resultsGroup.getName() + "_equityChart") + ".png";
                this.replace("Equity_Chart", "Equity chart", string4);
                string3 = this.file.getParentFile().getAbsolutePath() + "/" + string4;
            } else {
                string4 = this.escapeChartName(resultsGroup.getName() + "_" + string5) + ".png";
                object = (TradeAnalysisChart)TradeAnalysisChartsList.getInstance().findClassByName(string5);
                this.replace("Chart_" + n, ((TradeAnalysisChart)object).name, string4);
                string3 = this.file.getParentFile().getAbsolutePath() + "/" + string4;
                ++n;
            }
            object = Base64.decodeBase64((String)string6);
            try (FileOutputStream fileOutputStream = new FileOutputStream(string3);){
                ((OutputStream)fileOutputStream).write((byte[])object);
                ((OutputStream)fileOutputStream).close();
                continue;
            }
        }
    }

    private String escapeChartName(String string) {
        return string.replaceAll("[^a-zA-Z0-9_-]+", "_");
    }

    protected void resolveCharts(JSONObject jSONObject) throws Exception {
        try {
            this.chartsResolved = jSONObject.getJSONArray("charts");
        }
        finally {
            this.resolved = true;
        }
    }

    protected void addErrorsTable(ResultsGroup resultsGroup, String string) throws Exception {
        if (resultsGroup == null) {
            return;
        }
        int n = resultsGroup.specialValues().getInt("StrategyProblems", 0);
        if (n == 0) {
            return;
        }
        String string2 = "table.problems { width: 100%; background-color: #e0e2e3; color: #C00000; border: 1px solid #C00000;}\ntable.problems td { padding: 5px 5px 5px 30px; text-align: left; background-color: white; height: 15px; font-size: 11px;}\ntable.problems th { padding: 5px 5px 5px 10px; text-align: left; background-color: white; color: #606060; font-weight: normal; font-size: 11px;}\ntable.problems td.name {white-space: nowrap;}\n.problems h1 {color: #C00000; border-bottom: 0px;}";
        this.template = this.template.replace("</style>", string2 + "\n</style>");
        StringBuilder stringBuilder = new StringBuilder("<div class=\"problems\">");
        stringBuilder.append("<h1>Strategy Problems</h1>");
        stringBuilder.append("<table class=\"problems\" cellspacing=\"1\" cellpadding=\"0\" border=\"0\">");
        stringBuilder.append("<tr><th>SQ identified some problems when testing the strategy - strategy is most probably not suitable for trading on real account !<br/>These problems affect either strategy logic or accuracy of backtesting.</th></tr>");
        stringBuilder.append(this.printProblems(n, resultsGroup));
        stringBuilder.append("</table>");
        stringBuilder.append("</div>");
        stringBuilder.append("<br/><br/><br/>\n\n<div id=\"summaryBox\">");
        this.template = this.template.replace("<div id=\"summaryBox\">", stringBuilder.toString());
    }

    private String printProblems(int n, ResultsGroup resultsGroup) {
        StringBuilder stringBuilder = new StringBuilder("");
        if (resultsGroup.isStockpickerStrategy()) {
            this.printProblem(2048, n, stringBuilder);
        } else {
            this.printProblem(1, n, stringBuilder);
            this.printProblem(2, n, stringBuilder);
            this.printProblem(4, n, stringBuilder);
            this.printProblem(8, n, stringBuilder);
            this.printProblem(16, n, stringBuilder);
            this.printProblem(32, n, stringBuilder);
            this.printProblem(64, n, stringBuilder);
            this.printProblem(256, n, stringBuilder);
        }
        return stringBuilder.toString();
    }

    private void printProblem(int n, int n2, StringBuilder stringBuilder) {
        if ((n2 & n) != 0) {
            stringBuilder.append("<tr><td>");
            stringBuilder.append(BadStrategyException.getExplanation(n));
            stringBuilder.append("</td></tr>");
        }
    }

    public void replaceValues(ResultsGroup resultsGroup, String string, StatsTypeCombination statsTypeCombination) throws Exception {
        Object object;
        SQStats sQStats;
        Result result;
        block6: {
            result = null;
            sQStats = null;
            if (resultsGroup != null && (result = resultsGroup.subResult(string)) != null) {
                try {
                    sQStats = result.stats(statsTypeCombination);
                }
                catch (StatsDontExistException statsDontExistException) {
                    if (statsDontExistException.getMessage().contains("Result doesn't contain stats")) break block6;
                    Log.debug(statsDontExistException.getMessage());
                }
            }
        }
        String string2 = statsTypeCombination.getPLType() == 30 ? " small" : "";
        this.replace("Big", L.t((String)"TOTAL PROFIT", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("NetProfit"), statsTypeCombination.getPLType()), sQStats == null ? null : (sQStats.getDouble("NetProfit") > 0.0 ? "positiveNum" + string2 : "negativeNum" + string2));
        if (statsTypeCombination.getPLType() == 10) {
            this.replace("Small1", L.t((String)"PROFIT IN PIPS", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("NetProfitInPips"), (byte)30), sQStats == null ? null : (sQStats.getDouble("NetProfitInPips") > 0.0 ? "positiveNum" : "negativeNum"));
        } else {
            object = null;
            if (result != null) {
                object = result.stats(statsTypeCombination.getDirection(), (byte)10, statsTypeCombination.getSampleType());
            }
            this.replace("Small1", L.t((String)"PROFIT IN MONEY", (Object[])new Object[0]), object == null ? NA : this.d2WithPlType(((SQStats)object).getDouble("NetProfit"), (byte)10), object == null ? null : (((SQStats)object).getDouble("NetProfit") > 0.0 ? "positiveNum" : "negativeNum"));
        }
        this.replace("Small2", L.t((String)"YEARLY AVG PROFIT", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgProfitPerYear"), statsTypeCombination.getPLType()), sQStats == null ? null : (sQStats.getDouble("AvgProfitPerYear") > 0.0 ? "positiveNum" : "negativeNum"));
        this.replace("Small3", L.t((String)"YEARLY AVG % RETURN", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgPctProfitPerYear"), (byte)20), sQStats == null ? null : (sQStats.getDouble("AvgPctProfitPerYear") > 0.0 ? "positiveNum" : "negativeNum"));
        this.replace("Small4", L.t((String)"CAGR", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("CAGR"), (byte)20), sQStats == null ? null : (sQStats.getDouble("CAGR") > 0.0 ? "positiveNum" : "negativeNum"));
        this.replace("1_1", L.t((String)"# OF TRADES", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("NumberOfTrades"));
        this.replace("1_2", L.t((String)"SHARPE RATIO", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("SharpeRatio")));
        this.replace("1_3", L.t((String)"PROFIT FACTOR", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("ProfitFactor")));
        this.replace("1_4", L.t((String)"RETURN / DD RATIO", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("ReturnDDRatio")));
        this.replace("1_5", L.t((String)"WINNING PERCENTAGE", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("WinningPct")) + " %");
        object = statsTypeCombination.getPLType() == 20 ? "DrawdownPct" : (statsTypeCombination.getPLType() == 30 ? "DrawdownPips" : "Drawdown");
        this.replace("2_1", L.t((String)"DRAWDOWN", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble((String)object), statsTypeCombination.getPLType()));
        this.replace("2_2", L.t((String)"% DRAWDOWN", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("DrawdownPct"), (byte)20));
        this.replace("2_3", L.t((String)"DAILY AVG PROFIT", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgProfitPerDay"), statsTypeCombination.getPLType()));
        this.replace("2_4", L.t((String)"MONTHLY AVG PROFIT", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgProfitPerMonth"), statsTypeCombination.getPLType()));
        this.replace("2_5", L.t((String)"AVERAGE TRADE", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgTrade"), statsTypeCombination.getPLType()));
        this.replace("3_1", L.t((String)"ANNUAL % / Max DD %", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AnnualPctReturnDDRatio")));
        this.replace("3_2", L.t((String)"R EXPECTANCY", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("RExpectancy")));
        this.replace("3_3", L.t((String)"R EXPECTANCY SCORE", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("RExpectancyScore")));
        this.replace("3_4", L.t((String)"STR QUALITY NUMBER", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("SQN")));
        this.replace("3_5", L.t((String)"SQN SCORE", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("SQNScore")));
        this.replace("S1_1", L.t((String)"Wins / Losses Ratio", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("WinLossRatio")));
        this.replace("S1_2", L.t((String)"Payout Ratio (Avg Win/Loss)", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("PayoutRatio")));
        this.replace("S1_3", L.t((String)"Average # of Bars in Trade", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AvgBarsInTrade")));
        this.replace("S2_1", L.t((String)"AHPR", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AHPR")));
        this.replace("S2_2", L.t((String)"Z-Score", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("ZScore")));
        this.replace("S2_3", L.t((String)"Z-Probability", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("ZProbability")) + " %");
        this.replace("S3_1", L.t((String)"Expectancy", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("Expectancy")));
        this.replace("S3_2", L.t((String)"Deviation", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("StandardDev"), statsTypeCombination.getPLType()));
        this.replace("S3_3", L.t((String)"Exposure", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("Exposure", 0.0)) + " %");
        this.replace("S4_1", L.t((String)"Stagnation in Days", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("Stagnation"));
        this.replace("S4_2", L.t((String)"Stagnation in %", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("StagnationPct"), (byte)20));
        this.replace("S4_3", "", "");
        this.replace("T1_1", "", "");
        this.replace("T1_2", L.t((String)"# of Wins", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("NumberOfProfits"));
        this.replace("T1_3", L.t((String)"# of Losses", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("NumberOfLosses"));
        this.replace("T1_4", L.t((String)"# of Cancelled/Expired", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("NumberOfCanceled"));
        this.replace("T2_1", L.t((String)"Gross Profit", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("GrossProfit"), statsTypeCombination.getPLType()));
        this.replace("T2_2", L.t((String)"Gross Loss", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("GrossLoss"), statsTypeCombination.getPLType()));
        this.replace("T2_3", L.t((String)"Average Win", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgWin"), statsTypeCombination.getPLType()));
        this.replace("T2_4", L.t((String)"Average Loss", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("AvgLoss"), statsTypeCombination.getPLType()));
        this.replace("T3_1", L.t((String)"Largest Win", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("MaxProfit"), statsTypeCombination.getPLType()));
        this.replace("T3_2", L.t((String)"Largest Loss", (Object[])new Object[0]), sQStats == null ? NA : this.d2WithPlType(sQStats.getDouble("MaxLoss"), statsTypeCombination.getPLType()));
        this.replace("T3_3", L.t((String)"Max Consec Wins", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("MaxConsecWins"));
        this.replace("T3_4", L.t((String)"Max Consec Losses", (Object[])new Object[0]), sQStats == null ? NA : "" + sQStats.getInt("MaxConsecLosses"));
        this.replace("T4_1", L.t((String)"Avg Consec Wins", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AvgConsecWins")));
        this.replace("T4_2", L.t((String)"Avg Consec Loss", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AvgConsecLosses")));
        this.replace("T4_3", L.t((String)"Avg # of Bars in Wins", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AvgBarsWin")));
        this.replace("T4_4", L.t((String)"Avg # of Bars in Losses", (Object[])new Object[0]), sQStats == null ? NA : this.d2(sQStats.getDouble("AvgBarsLoss")));
        this.addMonthlyPerformanceTable(resultsGroup, string, statsTypeCombination);
        this.addTrades(resultsGroup, string, statsTypeCombination);
    }

    private void addTrades(ResultsGroup resultsGroup, String string, StatsTypeCombination statsTypeCombination) throws Exception {
        int n;
        StringBuilder stringBuilder = new StringBuilder("");
        OrdersList ordersList = resultsGroup.orders();
        TradelistTableView tradelistTableView = TradelistViewsManager.getInstance().getSelectedTradelistView();
        ArrayList<Object[]> arrayList = tradelistTableView.getData(ordersList, 0, ordersList.size(), true);
        int n2 = tradelistTableView.columns.size();
        stringBuilder.append("<tr class=\"tr" + L.t((String)"Trades", (Object[])new Object[0]) + "\">");
        for (n = 0; n < n2; ++n) {
            stringBuilder.append("<td>" + tradelistTableView.columns.get(n).getColumnEntryName() + "</td>");
        }
        stringBuilder.append("</tr>");
        for (n = 0; n < arrayList.size(); ++n) {
            if (this.format.equals("pdf") && n == 1000) {
                stringBuilder.append("<tr>");
                stringBuilder.append("<td colspan=\"" + tradelistTableView.columns.size() + "\">The trade list was shortened to 1000 rows (total " + arrayList.size() + ") to reduce file size.</td>");
                stringBuilder.append("</tr>");
                break;
            }
            stringBuilder.append("<tr>");
            Object[] objectArray = arrayList.get(n);
            for (int i = 0; i < tradelistTableView.columns.size(); ++i) {
                Object object = objectArray[i];
                TradelistTableColumnEntry tradelistTableColumnEntry = tradelistTableView.columns.get(i);
                try {
                    String string2 = this.formatValue(tradelistTableColumnEntry, String.valueOf(object), false);
                    if (n % 2 == 1) {
                        stringBuilder.append("<td bgcolor=\"#E0E0E0\">" + string2 + "</td>");
                        continue;
                    }
                    stringBuilder.append("<td >" + string2 + "</td>");
                    continue;
                }
                catch (Exception exception) {
                    stringBuilder.append("<td>N/A</td>");
                }
            }
            stringBuilder.append("</tr>");
        }
        this.template = this.template.replace("<!-- trades -->", stringBuilder.toString());
    }

    private String formatValue(TradelistTableColumnEntry tradelistTableColumnEntry, String string, boolean bl) {
        string = SQUtils.removeHtmlTags((String)string);
        if (bl) {
            switch (tradelistTableColumnEntry.tableColumn.getType()) {
                case "Integer": 
                case "Text": 
                case "Time": {
                    return string;
                }
            }
            return string.replace('.', ',');
        }
        return string;
    }

    private void addMonthlyPerformanceTable(ResultsGroup resultsGroup, String string, StatsTypeCombination statsTypeCombination) {
        String string2 = this.printTableBody(resultsGroup, string, statsTypeCombination);
        String string3 = "<div class=\"performance\"><h1>" + L.t((String)"Monthly Performance", (Object[])new Object[0]) + " (" + PlTypes.print(statsTypeCombination.getPLType()) + ")</h1><table class=\"calendar\" cellspacing=\"0\" cellpadding=\"0\" border=\"0\"><tr class=\"months\"><td>" + L.t((String)"Year", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Jan", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Feb", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Mar", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Apr", (Object[])new Object[0]) + "</td><td>" + L.t((String)"May", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Jun", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Jul", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Aug", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Sep", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Oct", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Nov", (Object[])new Object[0]) + "</td><td>" + L.t((String)"Dec", (Object[])new Object[0]) + "</td><td>" + L.t((String)"YTD", (Object[])new Object[0]) + "</td></tr>" + string2 + "</table></div>";
        this.template = this.template.replace("<!-- end of data -->", string3 + "\n<!-- end of data -->");
    }

    private String printTableBody(ResultsGroup resultsGroup, String string, StatsTypeCombination statsTypeCombination) {
        StringBuilder stringBuilder = new StringBuilder("");
        if (resultsGroup != null) {
            try {
                TreeMap<Integer, Double[]> treeMap = null;
                OrdersList ordersList = resultsGroup.orders().filter(string, statsTypeCombination.getDirection(), statsTypeCombination.getSampleType());
                treeMap = ReportGenerator.computeMonthlyPerformance(ordersList, statsTypeCombination.getPLType());
                int n = 0;
                for (Map.Entry entry : treeMap.descendingMap().entrySet()) {
                    String string2 = ((Integer)entry.getKey()).toString();
                    Double[] doubleArray = (Double[])entry.getValue();
                    String string3 = n % 2 == 0 ? "oddrow" : "evenrow";
                    stringBuilder.append("<tr class=\"" + string3 + "\">");
                    stringBuilder.append("<td class=\"bold\">" + string2 + "</td>");
                    for (int i = 0; i < doubleArray.length; ++i) {
                        if (doubleArray[i] < 0.0) {
                            stringBuilder.append("<td class=\"negativeNum\">" + this.d2(doubleArray[i]) + "</td>");
                            continue;
                        }
                        stringBuilder.append("<td>" + this.d2(doubleArray[i]) + "</td>");
                    }
                    stringBuilder.append("</tr>");
                    ++n;
                }
                return stringBuilder.toString();
            }
            catch (Exception exception) {
                Log.error("Cannot get list of orders. ", (Throwable)exception);
            }
        }
        return "<tr class=\"oddrow\"><td class=\"bold\">NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td></tr>";
    }

    public static TreeMap<Integer, Double[]> computeMonthlyPerformance(OrdersList ordersList, byte by) {
        TreeMap<Integer, Double[]> treeMap = new TreeMap<Integer, Double[]>();
        int n = -1;
        int n2 = -1;
        int n3 = -1;
        int n4 = -1;
        Double[] doubleArray = null;
        for (int i = 0; i < ordersList.size(); ++i) {
            Order object = ordersList.get(i);
            n3 = SQTime.getYear((long)object.CloseTime) + 1900;
            if (n == -1) {
                n = n3;
            }
            if (n2 == -1) {
                n2 = n3;
            }
            if (n > n3) {
                n = n3;
            }
            if (n2 < n3) {
                n2 = n3;
            }
            if (treeMap.containsKey(n3)) {
                doubleArray = treeMap.get(n3);
            } else {
                doubleArray = new Double[13];
                for (int j = 0; j < 13; ++j) {
                    doubleArray[j] = 0.0;
                }
                treeMap.put(n3, doubleArray);
            }
            n4 = SQTime.getMonth((long)object.CloseTime);
            Double[] d = doubleArray;
            int n5 = n4;
            Double.valueOf(d[n5] + (double)object.getPLByType(by));
        }
        for (Map.Entry entry : treeMap.entrySet()) {
            doubleArray = (Double[])entry.getValue();
            double d = 0.0;
            for (int i = 0; i < 12; ++i) {
                d += doubleArray[i].doubleValue();
            }
            doubleArray[12] = d;
        }
        if (n > 0 && n2 > 0) {
            for (n3 = n; n3 < n2; ++n3) {
                if (treeMap.containsKey(n3)) continue;
                doubleArray = new Double[13];
                for (int i = 0; i < 13; ++i) {
                    doubleArray[i] = 0.0;
                }
                treeMap.put(n3, doubleArray);
            }
        }
        return treeMap;
    }
}

