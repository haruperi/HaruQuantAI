/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.ChartSetup
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrderTypes
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.results.file.SQ3Settings
 *  org.jdom2.Attribute
 *  org.jdom2.Content
 *  org.jdom2.Document
 *  org.jdom2.Element
 */
package com.strategyquant.plugin.Saver.impl.SQ3;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrderTypes;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.results.file.SQ3Settings;
import java.io.File;
import java.util.Map;
import org.jdom2.Attribute;
import org.jdom2.Content;
import org.jdom2.Document;
import org.jdom2.Element;

public class SQ3FileSaver {
    public void save(ResultsGroup rg, String fileName, Map<String, String[]> parameterMap) throws Exception {
        Element elStrategyFile = new Element("StrategyFile");
        elStrategyFile.setAttribute(new Attribute("Version", "SQ " + MainApp.printAppVersion((boolean)false)));
        Document myDocument = new Document(elStrategyFile);
        elStrategyFile.addContent((Content)this.getStrategyXml(rg, parameterMap));
        Element elResults = new Element("TestResults");
        elStrategyFile.addContent((Content)elResults);
        elResults.addContent((Content)this.getResultsXml(rg, rg.isPortfolio() ? "Portfolio" : rg.getMainResultKey()));
        elResults.addContent((Content)this.getOrdersXml(rg, rg.isPortfolio() ? "Portfolio" : rg.getMainResultKey()));
        if (rg.isPortfolio()) {
            elResults.addContent((Content)this.getAdditionalData(rg));
        }
        File f = new File(fileName);
        XMLUtil.xmlToFile((Document)myDocument, (File)f);
    }

    protected String getParam(Map<String, String[]> params, String parameter, String defaultValue) throws Exception {
        if (params == null || !params.containsKey(parameter)) {
            return defaultValue;
        }
        return params.get(parameter)[0];
    }

    private Element getStrategyXml(ResultsGroup rg, Map<String, String[]> parameterMap) throws Exception {
        Element elStrategy = new Element("Strategy").setAttribute("portfolio", rg.isPortfolio() + "");
        String note = rg.specialValues().getString(SpecialValues.Note, "");
        boolean setNoteActive = Boolean.parseBoolean(this.getParam(parameterMap, "setNoteActive", "false"));
        if (setNoteActive) {
            String setNoteType = this.getParam(parameterMap, "setNoteType", "");
            String setNoteCustomText = this.getParam(parameterMap, "setNoteCustomText", "");
            String symbol = null;
            String timeframe = null;
            symbol = rg.mainResult().containsKey(SpecialValues.Symbol) ? rg.mainResult().getString(SpecialValues.Symbol) : rg.specialValues().getString(SpecialValues.Symbol, "N/A");
            timeframe = rg.mainResult().containsKey(SpecialValues.Timeframe) ? rg.mainResult().getString(SpecialValues.Timeframe) : rg.specialValues().getString(SpecialValues.Timeframe, "N/A");
            switch (setNoteType) {
                case "symbol": {
                    note = symbol;
                    break;
                }
                case "timeframe": {
                    note = timeframe;
                    break;
                }
                case "symbolTimeframe": {
                    note = symbol + "_" + timeframe;
                    break;
                }
                default: {
                    note = setNoteCustomText;
                }
            }
        }
        elStrategy.setAttribute("note", note);
        Element elStrategyNode = new Element("StrategyNode").setAttribute("Class", "com.sonarbytes.gn.geneng.nodes.special.StrategyNode");
        elStrategy.addContent((Content)elStrategyNode);
        Element elArray = new Element("Array");
        elStrategyNode.addContent((Content)elArray);
        elArray.addContent((Content)new Element("EmptyNode").setAttribute("Class", "com.sonarbytes.gn.geneng.nodes.special.EmptyNode"));
        elArray.addContent((Content)new Element("EmptyNode").setAttribute("Class", "com.sonarbytes.gn.geneng.nodes.special.EmptyNode"));
        elArray.addContent((Content)new Element("EmptyNode").setAttribute("Class", "com.sonarbytes.gn.geneng.nodes.special.EmptyNode"));
        elArray.addContent((Content)new Element("EmptyNode").setAttribute("Class", "com.sonarbytes.gn.geneng.nodes.special.EmptyNode"));
        return elStrategy;
    }

    private Element getSettingsXml(ResultsGroup rg, String resultKey) throws Exception {
        Element elSettingsFile = new Element("SettingsFile");
        elSettingsFile.setAttribute(new Attribute("Version", "1.0"));
        elSettingsFile.setAttribute(new Attribute("Name", ""));
        SQ3Settings settings = new SQ3Settings();
        elSettingsFile.addContent((Content)settings.convertToSQ3Xml(rg));
        return elSettingsFile;
    }

    private Element getOrdersXml(ResultsGroup rg, String resultKey) throws Exception {
        Element elOrders = new Element("Orders");
        elOrders.setAttribute(new Attribute("Version", "2.0"));
        if (!resultKey.equals("Portfolio")) {
            OrdersList filteredOL = rg.orders().filterExcludingControlOrders(resultKey, (byte)0, (byte)127, false);
            for (int i = 0; i < filteredOL.size(); ++i) {
                Order order = filteredOL.get(i);
                elOrders.addContent((Content)this.orderToXml(order));
            }
        }
        return elOrders;
    }

    private Element getResultsXml(ResultsGroup rg, String resultKey) throws Exception {
        Element resultsEl = new Element("Results");
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "InSample", (byte)10, (byte)10));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "OutOfSample", (byte)10, (byte)20));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "FullSample", (byte)10, (byte)127));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "InSampleTicks", (byte)30, (byte)10));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "OutOfSampleTicks", (byte)30, (byte)20));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "FullSampleTicks", (byte)30, (byte)127));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "InSamplePct", (byte)20, (byte)10));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "OutOfSamplePct", (byte)20, (byte)20));
        resultsEl.addContent((Content)this.getStatsDataXml(rg, resultKey, "FullSamplePct", (byte)20, (byte)127));
        resultsEl.addContent((Content)this.getSettingsXml(rg, resultKey));
        return resultsEl;
    }

    private Element getStatsDataXml(ResultsGroup rg, String resultKey, String name, byte plType, byte sampleType) throws Exception {
        Result result = rg.subResult(resultKey);
        Element statsDataEl = new Element("StatsData");
        statsDataEl.setAttribute("SampleType", name);
        statsDataEl.addContent((Content)this.getValuesXml(0, result.statsOrNull((byte)0, plType, sampleType)));
        statsDataEl.addContent((Content)this.getValuesXml(1, result.statsOrNull((byte)0, plType, sampleType)));
        statsDataEl.addContent((Content)this.getValuesXml(2, result.statsOrNull((byte)0, plType, sampleType)));
        return statsDataEl;
    }

    public Element getValuesXml(int index, SQStats stats) {
        Element values = new Element("Values");
        values.setAttribute("Index", Integer.valueOf(index).toString());
        if (stats == null) {
            return values;
        }
        values.addContent((Content)new Element("netProfit").addContent(stats.getDouble("NetProfit") + ""));
        values.addContent((Content)new Element("numberOfTrades").addContent(stats.getInt("NumberOfTrades") + ""));
        values.addContent((Content)new Element("pctWins").addContent(stats.getDouble("WinningPct") + ""));
        values.addContent((Content)new Element("profitFactor").addContent(stats.getDouble("ProfitFactor") + ""));
        values.addContent((Content)new Element("drawdown").addContent(stats.getDouble("Drawdown") + ""));
        values.addContent((Content)new Element("pctDrawdown").addContent(stats.getDouble("DrawdownPct") + ""));
        values.addContent((Content)new Element("winLossRatio").addContent(stats.getDouble("WinLossRatio") + ""));
        values.addContent((Content)new Element("retDDRatio").addContent(stats.getDouble("ReturnDDRatio") + ""));
        values.addContent((Content)new Element("avgWin").addContent(stats.getDouble("AvgWin") + ""));
        values.addContent((Content)new Element("avgLoss").addContent(stats.getDouble("AvgLoss") + ""));
        values.addContent((Content)new Element("avgBarsWin").addContent(stats.getDouble("AvgBarsWin") + ""));
        values.addContent((Content)new Element("avgBarsLoss").addContent(stats.getDouble("AvgBarsLoss") + ""));
        values.addContent((Content)new Element("avgTrade").addContent(stats.getDouble("AvgTrade") + ""));
        values.addContent((Content)new Element("avgBarsTrade").addContent(stats.getDouble("AvgBarsInTrade") + ""));
        values.addContent((Content)new Element("payoutRatio").addContent(stats.getDouble("PayoutRatio") + ""));
        values.addContent((Content)new Element("numberOfWins").addContent(stats.getInt("NumberOfProfits") + ""));
        values.addContent((Content)new Element("numberOfLoss").addContent(stats.getInt("NumberOfLosses") + ""));
        values.addContent((Content)new Element("grossProfit").addContent(stats.getDouble("GrossProfit") + ""));
        values.addContent((Content)new Element("grossLoss").addContent(stats.getDouble("GrossLoss") + ""));
        values.addContent((Content)new Element("largestWin").addContent(stats.getDouble("MaxProfit") + ""));
        values.addContent((Content)new Element("largestLoss").addContent(stats.getDouble("MaxLoss") + ""));
        values.addContent((Content)new Element("maxConsecWins").addContent(stats.getInt("MaxConsecWins") + ""));
        values.addContent((Content)new Element("maxConsecLoss").addContent(stats.getInt("MaxConsecLosses") + ""));
        values.addContent((Content)new Element("avgConsecWin").addContent(stats.getDouble("AvgConsecWins") + ""));
        values.addContent((Content)new Element("avgConsecLoss").addContent(stats.getDouble("AvgConsecLosses") + ""));
        values.addContent((Content)new Element("correlation").addContent(stats.getDouble("Correlation") + ""));
        values.addContent((Content)new Element("symmetry").addContent(stats.getDouble("Symmetry") + ""));
        values.addContent((Content)new Element("ordersHash").addContent("0"));
        values.addContent((Content)new Element("exposure").addContent(stats.getDouble("Exposure") + ""));
        values.addContent((Content)new Element("stagnationFrom").addContent(stats.getLong("StagnationFrom") / 1000L + ""));
        values.addContent((Content)new Element("stagnationTo").addContent(stats.getLong("StagnationTo") / 1000L + ""));
        values.addContent((Content)new Element("stagnationPeriod").addContent(stats.getInt("Stagnation") + ""));
        values.addContent((Content)new Element("stagnationPeriodPct").addContent(stats.getDouble("StagnationPct") + ""));
        values.addContent((Content)new Element("degreesOfFreedom").addContent(stats.getInt("DegreesOfFreedom") + ""));
        values.addContent((Content)new Element("complexity").addContent("0"));
        values.addContent((Content)new Element("AHPR").addContent(stats.getDouble("AHPR") + ""));
        values.addContent((Content)new Element("sharpeRatio").addContent(stats.getDouble("SharpeRatio") + ""));
        values.addContent((Content)new Element("pctLoss").addContent("0"));
        values.addContent((Content)new Element("expectancy").addContent(stats.getDouble("Expectancy") + ""));
        values.addContent((Content)new Element("standardDev").addContent(stats.getDouble("StandardDev") + ""));
        values.addContent((Content)new Element("zProbability").addContent(stats.getDouble("ZProbability") + ""));
        values.addContent((Content)new Element("zScore").addContent(stats.getDouble("ZScore") + ""));
        values.addContent((Content)new Element("avgProfitByDay").addContent(stats.getDouble("AvgProfitPerDay") + ""));
        values.addContent((Content)new Element("avgProfitByMonth").addContent(stats.getDouble("AvgProfitPerMonth") + ""));
        values.addContent((Content)new Element("avgProfitByYear").addContent(stats.getDouble("AvgProfitPerYear") + ""));
        values.addContent((Content)new Element("rexpectancy").addContent(stats.getDouble("RExpectancy") + ""));
        values.addContent((Content)new Element("rexpectancyopp").addContent(stats.getDouble("RExpectancyScore") + ""));
        values.addContent((Content)new Element("aarDDRatio").addContent(stats.getDouble("AnnualPctReturnDDRatio") + ""));
        values.addContent((Content)new Element("avgPctProfitByYear").addContent("0"));
        values.addContent((Content)new Element("avgPctProfitByMonth").addContent("0"));
        values.addContent((Content)new Element("sqn").addContent(stats.getDouble("SQN") + ""));
        values.addContent((Content)new Element("sqn_score").addContent(stats.getDouble("SQNScore") + ""));
        values.addContent((Content)new Element("reached100PctDD").addContent("0"));
        values.addContent((Content)new Element("totalDaysOfTrading").addContent(stats.getInt("TotalTradingDays") + ""));
        return values;
    }

    private Element orderToXml(Order order) {
        Element elOrder = new Element("Order");
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)order.Symbol);
        elOrder.addContent((Content)new Element("ticket").addContent(order.Ticket + ""));
        elOrder.addContent((Content)new Element("type").addContent(order.Type + ""));
        elOrder.addContent((Content)new Element("originalType").addContent(order.OriginalType + ""));
        elOrder.addContent((Content)new Element("volume").addContent(order.Size + ""));
        elOrder.addContent((Content)new Element("openPrice").addContent(order.OpenPrice + ""));
        elOrder.addContent((Content)new Element("closePrice").addContent(order.ClosePrice + ""));
        elOrder.addContent((Content)new Element("stoploss").addContent(order.StopLoss + ""));
        elOrder.addContent((Content)new Element("takeprofit").addContent(order.TakeProfit + ""));
        elOrder.addContent((Content)new Element("openTime").addContent(order.OpenTime / 1000L + ""));
        elOrder.addContent((Content)new Element("closeTime").addContent(order.CloseTime / 1000L + ""));
        elOrder.addContent((Content)new Element("closeType").addContent(order.CloseType + ""));
        elOrder.addContent((Content)new Element("barsInTrade").addContent(order.BarsInTrade + ""));
        elOrder.addContent((Content)new Element("pl").addContent(order.PL + ""));
        elOrder.addContent((Content)new Element("pctPL").addContent(order.PctPL + ""));
        elOrder.addContent((Content)new Element("pipsPL").addContent(order.PipsPL + ""));
        elOrder.addContent((Content)new Element("outOfSample").addContent((order.Type == 20) + ""));
        elOrder.addContent((Content)new Element("inSampleValidation").addContent("false"));
        elOrder.addContent((Content)new Element("status").addContent("0"));
        double mae = 0.0;
        double mfe = 0.0;
        if (dataInfo != null && mae != 0.0 && mfe != 0.0) {
            if (OrderTypes.isLongOrder((byte)order.Type)) {
                mae = this.moneyToPips(-1.0f * order.MAE, dataInfo, order) * dataInfo.symbolInfo.tickSize + (double)order.OpenPrice;
                mfe = this.moneyToPips(order.MFE, dataInfo, order) * dataInfo.symbolInfo.tickSize + (double)order.OpenPrice;
            } else {
                mae = this.moneyToPips(-1.0f * order.MAE, dataInfo, order) * dataInfo.symbolInfo.tickSize - (double)order.OpenPrice;
                mfe = this.moneyToPips(order.MFE, dataInfo, order) * dataInfo.symbolInfo.tickSize - (double)order.OpenPrice;
            }
        }
        elOrder.addContent((Content)new Element("mae").addContent(Math.abs(mae) + ""));
        elOrder.addContent((Content)new Element("mfe").addContent(Math.abs(mfe) + ""));
        elOrder.addContent((Content)new Element("dd").addContent(order.DD + ""));
        elOrder.addContent((Content)new Element("pctDD").addContent(order.PctDD + ""));
        elOrder.addContent((Content)new Element("pipsDD").addContent(order.PipsDD + ""));
        elOrder.addContent((Content)new Element("commSwap").addContent(-order.CommSwap + ""));
        return elOrder;
    }

    private double moneyToPips(double value, DataInfo dataInfo, Order order) {
        return value / (double)order.Size / dataInfo.symbolInfo.pointValue / dataInfo.symbolInfo.tickSize;
    }

    private Element getAdditionalData(ResultsGroup rg) throws Exception {
        Element elAdditionalDataResults = new Element("AdditionalDataResults");
        Element elPortfolioResult = new Element("PortfolioResult");
        elPortfolioResult.addContent((Content)this.getAdditionalDataResult(rg, "Portfolio"));
        elAdditionalDataResults.addContent((Content)elPortfolioResult);
        Element elAdResults = new Element("AdResults");
        elAdditionalDataResults.addContent((Content)elAdResults);
        for (String resultKey : rg.getResultKeys()) {
            if (resultKey.equals("Portfolio")) continue;
            elAdResults.addContent((Content)this.getAdditionalDataResult(rg, resultKey));
        }
        return elAdditionalDataResults;
    }

    private Element getAdditionalDataResult(ResultsGroup rg, String resultKey) throws Exception {
        ChartDef chart;
        Result result = rg.subResult(resultKey);
        Element elAdditionalDataResult = new Element("AdditionalDataResult");
        SettingsMap settings = rg.portfolio().getSettings();
        ChartSetup chartSetup = settings == null ? null : (ChartSetup)settings.get("BacktestChart");
        ChartDef chartDef = chart = chartSetup == null ? null : (ChartDef)chartSetup.getCharts().get(0);
        if (!resultKey.equals("Portfolio")) {
            elAdditionalDataResult.addContent((Content)new Element("generationId").addContent(resultKey));
            elAdditionalDataResult.addContent((Content)new Element("symbol").addContent(resultKey));
            String timeframe = chart == null ? null : chart.getTimeframe();
            elAdditionalDataResult.addContent((Content)new Element("timeframe").addContent(SQ3Settings.translateSQ4TFToInt((String)timeframe) + ""));
            elAdditionalDataResult.addContent((Content)new Element("dateFrom").addContent(chart == null ? "0" : chart.getHistoryFrom() / 1000L + ""));
            elAdditionalDataResult.addContent((Content)new Element("dateTo").addContent(chart == null ? "0" : chart.getHistoryTo() / 1000L + ""));
            elAdditionalDataResult.addContent((Content)new Element("testPrecision").addContent("1"));
            elAdditionalDataResult.addContent((Content)new Element("spread").addContent("3"));
            elAdditionalDataResult.addContent((Content)new Element("slippage").addContent("0"));
            elAdditionalDataResult.addContent((Content)new Element("minDistance").addContent("5"));
            elAdditionalDataResult.addContent((Content)this.getOrdersXml(rg, resultKey));
        }
        Element elAdditionalStrategyStatsData = new Element("AdditionalStrategyStatsData");
        elAdditionalDataResult.addContent((Content)elAdditionalStrategyStatsData);
        Element elValuesAll = new Element("ValuesAll");
        elAdditionalStrategyStatsData.addContent((Content)elValuesAll);
        elValuesAll.addContent((Content)this.getValuesXml(0, result.stats((byte)0, (byte)10, (byte)127)));
        Element elValuesLong = new Element("ValuesLong");
        elAdditionalStrategyStatsData.addContent((Content)elValuesLong);
        elValuesLong.addContent((Content)this.getValuesXml(0, result.stats((byte)1, (byte)10, (byte)127)));
        Element elValuesShort = new Element("ValuesShort");
        elAdditionalStrategyStatsData.addContent((Content)elValuesShort);
        elValuesShort.addContent((Content)this.getValuesXml(0, result.stats((byte)-1, (byte)10, (byte)127)));
        return elAdditionalDataResult;
    }
}

