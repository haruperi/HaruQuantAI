/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.AbstractChart
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.TradeAnalysisChart
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.tradeanalysis.TradeAnalysisChartsList
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.TradeAnalysis;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.Results.impl.TradeAnalysis.AnnualStatsComputer;
import com.strategyquant.tradinglib.AbstractChart;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.TradeAnalysisChart;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.tradeanalysis.TradeAnalysisChartsList;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradeAnalysisServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(TradeAnalysisServlet.class);
    private static final String LOCK_TRADEANALYSISSERVLET = "TradeAnalysisServlet";
    private static IResultsGroupProvider rgProvider;
    private AnnualStatsComputer statsComputer = new AnnualStatsComputer();
    private static final String SettingKey = "TradeAnalysisCharts";
    public ResultsGroup rg = null;

    public TradeAnalysisServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(args);
            }
            case "getAnnualStats": {
                return this.onGetAnnualStats(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONArray loadLastSettings() throws Exception {
        String charts = MainApp.settings().get(SettingKey, null);
        if (charts == null || charts.split(",").length < 12) {
            charts = "PLbyHourChart,PLbyWeekdayChart,TradesByWeekdayChart,LongShortProfitLossChart,WinLossCountByWeekdayChart,WinLossPLByMonthChart,LongShortTradesChart,PLGrowthByDurationChart,TradesByHourChart,PLLongChart,PLShortChart,TradesByDurationChart";
        }
        return SQUtils.toJSONArray((String)charts);
    }

    public JSONArray getTypes() throws Exception {
        JSONArray types = new JSONArray();
        for (TradeAnalysisChart type : TradeAnalysisChartsList.getInstance().getAvailableClasses()) {
            String className = type.getClass().getSimpleName();
            if (className.equals("PLbyYearChart")) continue;
            JSONObject item = new JSONObject();
            item.put("type", (Object)className);
            item.put("name", (Object)type.toString());
            types.put((Object)item);
        }
        return types;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"resultKey", "direction", "sampleType", "charts"});
        String chartTypes = this.tryGetParamValue(parameterMap, "charts");
        String[] chartsItems = chartTypes.split(",");
        JSONObject response = new JSONObject();
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = this.rg == null ? rgProvider.get(parameterMap, LOCK_TRADEANALYSISSERVLET) : this.rg;
            String _resultkey = parameterMap.get("resultKey")[0].toString();
            byte _direction = Byte.parseByte(parameterMap.get("direction")[0]);
            byte _sampleType = Byte.parseByte(parameterMap.get("sampleType")[0]);
            OrdersList orders = resultsGroup.orders().filterExcludingControlOrders(_resultkey, _direction, _sampleType, true);
            JSONArray charts = new JSONArray();
            for (int i = 0; i < chartsItems.length; ++i) {
                JSONObject chart = this.printChart(parameterMap, orders, chartsItems[i]);
                charts.put((Object)chart);
            }
            MainApp.settings().set(SettingKey, chartTypes);
            response.put("charts", (Object)charts);
            JSONObject chart = this.printChart(parameterMap, orders, "PLbyYearChart");
            response.put("fixedChart", (Object)chart);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = TradeAnalysisServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = TradeAnalysisServlet.apiErrorJSON((String)L.t((String)"Getting trade analysis failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null && this.rg == null) {
                resultsGroup.releaseLock(LOCK_TRADEANALYSISSERVLET);
                resultsGroup = null;
                this.rg = null;
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONObject printChart(Map<String, String[]> parameterMap, OrdersList orders, String type) throws Exception {
        TradeAnalysisChart tradeAnalysisChart = (TradeAnalysisChart)TradeAnalysisChartsList.getInstance().findClassByName(type);
        byte _tradePeriod = Byte.parseByte(parameterMap.get("period")[0]);
        String _year = parameterMap.get("year")[0].toString();
        AbstractChart chart = null;
        if (!_year.equals("All")) {
            int year = Integer.parseInt(_year);
            OrdersList ordersNew = new OrdersList("filteredByYear");
            for (int i = 0; i < orders.size(); ++i) {
                Order order = orders.get(i);
                if (year != SQTime.getFullYear((long)order.getTimeByPeriodType(_tradePeriod))) continue;
                ordersNew.add(order);
            }
            chart = tradeAnalysisChart.draw(ordersNew, (byte)10, _tradePeriod);
            ordersNew.clear();
        } else {
            chart = tradeAnalysisChart.draw(orders, (byte)10, _tradePeriod);
        }
        return chart.toJSON();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetAnnualStats(Map<String, String[]> parameterMap) throws Exception {
        OrdersList filteredOL;
        this.checkParamExists(parameterMap, new String[]{"project", "databank", "strategy", "resultKey", "direction", "sampleType"});
        String _resultkey = parameterMap.get("resultKey")[0].toString();
        byte _direction = Byte.parseByte(parameterMap.get("direction")[0]);
        byte _sampleType = Byte.parseByte(parameterMap.get("sampleType")[0]);
        byte _tradingPeriod = Byte.parseByte(parameterMap.get("period")[0]);
        JSONObject response = new JSONObject();
        JSONArray data = new JSONArray();
        OrdersList orders = null;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_TRADEANALYSISSERVLET);
            orders = resultsGroup.orders();
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = TradeAnalysisServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_TRADEANALYSISSERVLET);
            }
        }
        if (orders != null && (filteredOL = resultsGroup.orders().filterExcludingControlOrders(_resultkey, _direction, _sampleType, true)).size() > 0) {
            long dateFrom = -1L;
            long dateTo = -1L;
            for (int i = 0; i < filteredOL.size(); ++i) {
                Order order = filteredOL.get(i);
                if (dateFrom == -1L || dateFrom > order.OpenTime) {
                    dateFrom = order.OpenTime;
                }
                if (dateTo != -1L && dateTo >= order.CloseTime) continue;
                dateTo = order.CloseTime;
            }
            int yearFrom = SQTime.getFullYear((long)dateFrom);
            int yearTo = SQTime.getFullYear((long)dateTo);
            data.put((Object)this.calculateAnnualStats(0, filteredOL, (byte)10, _tradingPeriod));
            for (int year = yearTo; year >= yearFrom; --year) {
                data.put((Object)this.calculateAnnualStats(year, filteredOL, (byte)10, _tradingPeriod));
            }
        }
        response.put("rows", (Object)data);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONObject calculateAnnualStats(int year, OrdersList orders, byte plType, byte tradePeriod) {
        JSONObject row = new JSONObject();
        JSONArray rowData = this.statsComputer.compute(year, orders, (byte)10, tradePeriod);
        row.put("id", (Object)("r" + year));
        row.put("data", (Object)rowData);
        return row;
    }
}

