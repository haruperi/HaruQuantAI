/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.WalkForwardResult
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.equitychart.Equity
 *  com.strategyquant.tradinglib.equitychart.EquityChart
 *  com.strategyquant.tradinglib.equitychart.EquityChartUtils
 *  com.strategyquant.tradinglib.equitychart.MainChartDataset
 *  com.strategyquant.tradinglib.equitychart.MaxNewHighDuration
 *  com.strategyquant.tradinglib.equitychart.Periods
 *  com.strategyquant.tradinglib.equitychart.Points
 *  com.strategyquant.tradinglib.equitychart.SampleMarkers
 *  com.strategyquant.tradinglib.equitychart.Stagnation
 *  com.strategyquant.tradinglib.equitychart.TrendLines
 *  com.strategyquant.tradinglib.equitychart.WalkForward
 *  com.strategyquant.tradinglib.equitychart.YearMarkers
 *  com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon
 *  com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime
 *  com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.EquityChart;

import com.strategyquant.lib.L;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.WalkForwardResult;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.equitychart.Equity;
import com.strategyquant.tradinglib.equitychart.EquityChart;
import com.strategyquant.tradinglib.equitychart.EquityChartUtils;
import com.strategyquant.tradinglib.equitychart.MainChartDataset;
import com.strategyquant.tradinglib.equitychart.MaxNewHighDuration;
import com.strategyquant.tradinglib.equitychart.Periods;
import com.strategyquant.tradinglib.equitychart.Points;
import com.strategyquant.tradinglib.equitychart.SampleMarkers;
import com.strategyquant.tradinglib.equitychart.Stagnation;
import com.strategyquant.tradinglib.equitychart.TrendLines;
import com.strategyquant.tradinglib.equitychart.WalkForward;
import com.strategyquant.tradinglib.equitychart.YearMarkers;
import com.strategyquant.tradinglib.equitychartnew.addons.IEquityChartAddon;
import com.strategyquant.tradinglib.optimization.WalkForwardMatrixResult;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByCloseTime;
import com.strategyquant.tradinglib.results.stats.comparator.OrderComparatorByOpenTime;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class EquityChartServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(EquityChartServlet.class);
    private static final DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyy-MM-dd");
    private static final String LOCK_EQUITYCHARTSERVLET = "EquityChartServlet";
    private EquityChart chart = null;
    private Periods periods = null;
    private YearMarkers yearMarkers = null;
    private SampleMarkers sampleMarkers = null;
    private TrendLines trendLines = null;
    private Points points = null;
    private Stagnation stagnation = null;
    private MaxNewHighDuration maxNewHighDuration = null;
    private WalkForward walkForward = null;
    private Equity equity = null;
    private IResultsGroupProvider rgProvider;
    private final Comparator<Order> comparatorByCloseTime = new OrderComparatorByCloseTime();
    private final Comparator<Order> comparatorByOpenTime = new OrderComparatorByOpenTime();
    private static final String SettingKey = "EquityChart";
    public ResultsGroup rg = null;

    public EquityChartServlet(IResultsGroupProvider rgProvider) {
        this.chart = new EquityChart();
        this.periods = new Periods();
        this.yearMarkers = new YearMarkers();
        this.sampleMarkers = new SampleMarkers();
        this.trendLines = new TrendLines();
        this.points = new Points();
        this.stagnation = new Stagnation();
        this.maxNewHighDuration = new MaxNewHighDuration();
        this.walkForward = new WalkForward();
        this.equity = new Equity();
        this.rgProvider = rgProvider;
    }

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONObject loadLastSettings() throws Exception {
        String[] items;
        JSONObject data = new JSONObject();
        String settings = MainApp.settings().get(SettingKey, null);
        if (settings != null && (items = settings.split(",")).length == 11) {
            data.put("xAxisType", (Object)items[0]);
            data.put("drawdown", (Object)items[1]);
            data.put("volume", (Object)items[2]);
            data.put("stagnation", (Object)items[3]);
            data.put("maxNewHighDuration", (Object)items[4]);
            data.put("equity", (Object)items[5]);
            data.put("yearmarker", (Object)items[6]);
            data.put("trendline", (Object)Boolean.valueOf(items[7]));
            data.put("points", (Object)items[8]);
            data.put("dailychart", items.length > 8 ? Boolean.valueOf(items[9]) : false);
            data.put("volatility", items.length > 8 ? Boolean.valueOf(items[10]) : false);
            data.put("benchmarkActive", items.length == 12 ? Boolean.valueOf(items[11]) : false);
            data.put("benchmarkSymbol", (Object)(items.length == 13 ? items[12] : "SPY.D"));
            data.put("benchmarkNormalization", (Object)(items.length == 12 ? items[11] : "exposure"));
        }
        return data;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private synchronized String onPrint(Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"direction", "sampleType", "width"});
        ResultsGroup resultsGroup = null;
        JsonCreator json = new JsonCreator();
        try {
            String special = null;
            String _resultkey = this.tryGetParam(parameterMap, "resultKey")[0];
            if ("Portfolio only".equals(_resultkey) || "Portfolio parts only".equals(_resultkey)) {
                special = _resultkey;
                _resultkey = "Portfolio";
            }
            byte _direction = Byte.parseByte(parameterMap.get("direction")[0]);
            byte _sampleType = Byte.parseByte(parameterMap.get("sampleType")[0]);
            String _xAxisType = parameterMap.get("xaxis")[0].toString();
            byte _drawdown = Byte.parseByte(parameterMap.get("drawdown")[0]);
            byte _volume = Byte.parseByte(parameterMap.get("volume")[0]);
            byte _stagnation = Byte.parseByte(parameterMap.get("stagnation")[0]);
            byte _maxNewHighDuration = Byte.parseByte(parameterMap.containsKey("maxNewHighDuration") ? parameterMap.get("maxNewHighDuration")[0] : "0");
            String _equity = parameterMap.get("equity")[0].toString();
            Boolean _yearmarker = true;
            Boolean _trendline = Boolean.parseBoolean(parameterMap.get("trendline")[0]);
            String _points = parameterMap.get("points")[0].toString();
            int _width = Integer.parseInt(parameterMap.get("width")[0]);
            boolean zoom = Boolean.parseBoolean(parameterMap.get("zoom")[0]);
            int zoomwidth = Integer.parseInt(parameterMap.get("zoomwidth")[0]);
            boolean isTime = "time".equals(_xAxisType) || "Portfolio".equals(_resultkey);
            long zoomminX = isTime ? this.parseTime(parameterMap.get("zoomminX")[0]) : this.parseLong(parameterMap.get("zoomminX")[0]);
            long zoommaxX = isTime ? this.parseTime(parameterMap.get("zoommaxX")[0]) : this.parseLong(parameterMap.get("zoommaxX")[0]);
            boolean dailychart = Boolean.parseBoolean(parameterMap.get("dailychart")[0]);
            boolean volatility = Boolean.parseBoolean(parameterMap.get("volatility")[0]);
            boolean benchmarkActive = Boolean.parseBoolean(parameterMap.get("benchmarkActive")[0]);
            String benchmarkSymbol = parameterMap.get("benchmarkSymbol")[0].toString();
            String benchmarkNormalization = parameterMap.get("benchmarkNormalization")[0].toString();
            this.saveLastSettings(_xAxisType, _drawdown, _volume, _stagnation, _maxNewHighDuration, _equity, _yearmarker, _trendline, _points, dailychart, volatility, benchmarkActive, benchmarkSymbol, benchmarkNormalization);
            if (!zoom) {
                zoomwidth = _width;
            }
            if (zoomwidth < 1024) {
                zoomwidth = 1024;
            }
            json.beginObject();
            this.chart.reset();
            this.chart.setPLType((byte)10);
            this.chart.zoom(zoom, zoomwidth, zoomminX, zoommaxX);
            if (_resultkey != null) {
                String[] parts = _resultkey.split(":");
                this.chart.setCornerCaption(parts.length == 2 ? parts[1] : _resultkey);
            }
            resultsGroup = this.rg == null ? this.rgProvider.get(parameterMap, LOCK_EQUITYCHARTSERVLET) : this.rg;
            OrdersList orders = resultsGroup.orders().filterExcludingControlOrders(_resultkey, _direction, _sampleType, true);
            orders.sort(this.comparatorByCloseTime);
            this.chart.setDomainAxisType(_xAxisType);
            if (_resultkey.equals("Portfolio")) {
                String mainKey = resultsGroup.getMainResultKey();
                List datasets = EquityChartUtils.generatePorfolioDatasets((ResultsGroup)resultsGroup, (byte)_direction, (byte)_sampleType, (String)special, (String)_xAxisType);
                for (int i = 0; i < datasets.size(); ++i) {
                    MainChartDataset dataset = (MainChartDataset)datasets.get(i);
                    this.chart.addMainChartDataset(dataset);
                    if (dataset.name.equals("Portfolio")) {
                        dataset.thickness = 3;
                        dataset.filled = true;
                        dataset.fillColor = "#DAF5FF";
                        dataset.fillColorDark = "#333C63";
                        dataset.fillNegativeColor = "#F49C9C";
                        continue;
                    }
                    if (special != null && special.equals("Portfolio parts only") && dataset.name.equals(mainKey) && mainKey.startsWith("Main:")) {
                        dataset.thickness = 3;
                        continue;
                    }
                    if (special != null || !dataset.name.equals(mainKey) || !mainKey.startsWith("Main:")) continue;
                    dataset.thickness = 3;
                }
                json.put("portfolio", (Object)true, true);
            } else {
                MainChartDataset dataset = EquityChartUtils.generateDataset((OrdersList)orders, (String)_xAxisType);
                dataset.title = "Balance";
                dataset.filled = true;
                dataset.fillColor = "#DAF5FF";
                dataset.fillNegativeColor = "#F49C9C";
                dataset.fillColorDark = "#333C63";
                dataset.thickness = 1;
                this.chart.addMainChartDataset(dataset);
                json.put("portfolio", (Object)false, true);
            }
            json.put("stockPick", (Object)(resultsGroup != null && resultsGroup.isStockpickerStrategy() ? 1 : 0), true);
            orders.sort(this.comparatorByOpenTime);
            boolean showOOS = true;
            List periodList = this.periods.getAvailablePeriods(orders, _xAxisType);
            if (periodList.size() > 10) {
                if (_resultkey.equals("Portfolio")) {
                    showOOS = false;
                }
            }
            orders.sort(this.comparatorByCloseTime);
            if (_yearmarker.booleanValue()) {
                this.yearMarkers.print(this.chart, orders, _xAxisType);
            }
            if ((_sampleType == 127 || _sampleType == 10) && !this.isWFResult(resultsGroup, _resultkey) && showOOS) {
                this.sampleMarkers.print(this.chart, periodList, true);
            }
            if (_trendline.booleanValue() && showOOS) {
                this.trendLines.print(this.chart, periodList, _xAxisType);
            }
            if (!_points.equals("off")) {
                this.points.print(this.chart, _points, _xAxisType);
            }
            if (special == null || !special.equals("Portfolio parts only")) {
                this.equity.print(this.chart, orders, resultsGroup, _xAxisType, _resultkey, _direction, _sampleType, _equity);
            }
            if (_stagnation != 0) {
                this.stagnation.print(this.chart, resultsGroup, _resultkey, orders, _direction, (byte)10, _stagnation, _xAxisType);
            }
            if (_maxNewHighDuration != 0) {
                this.maxNewHighDuration.print(this.chart, resultsGroup, _resultkey, orders, _direction, (byte)10, _maxNewHighDuration, _xAxisType);
            }
            for (IEquityChartAddon addon : SQPluginManager.getPlugins(IEquityChartAddon.class)) {
                try {
                    addon.print(this.chart, resultsGroup, _resultkey, orders, parameterMap, _xAxisType);
                }
                catch (Exception e) {
                    Log.error("Error while rendering EquityChart addon '" + addon.getName() + "'. Exc.", (Throwable)e);
                }
            }
            this.walkForward.print(this.chart, orders, resultsGroup, _xAxisType, _resultkey, _direction, _sampleType);
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = EquityChartServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        catch (Exception e) {
            String string = EquityChartServlet.apiErrorJSON((String)L.t((String)"Loading equity chart failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (resultsGroup != null && this.rg == null) {
                resultsGroup.releaseLock(LOCK_EQUITYCHARTSERVLET);
                resultsGroup = null;
                this.rg = null;
            }
        }
        json.putBeginObject("chart");
        this.chart.fillJSON(json);
        json.endObject(true);
        json.put("success", (Object)"ok", false);
        json.endObject(false);
        return json.toJson();
    }

    private void saveLastSettings(String xAxisType, byte drawdown, byte volume, byte stagnation, byte maxNewHighDuration, String equity, Boolean yearmarker, Boolean trendline, String points, Boolean dailychart, Boolean volatility, Boolean benchmarkActive, String benchmarkSymbol, String benchmarkNormalization) {
        String text = xAxisType + "," + drawdown + "," + volume + "," + stagnation + "," + maxNewHighDuration + "," + equity + "," + yearmarker + "," + trendline + "," + points + "," + dailychart + "," + volatility + "," + benchmarkActive + "," + benchmarkSymbol + "," + benchmarkNormalization;
        MainApp.settings().set(SettingKey, text);
    }

    private boolean isWFResult(ResultsGroup resultsGroup, String resultkey) throws Exception {
        WalkForwardMatrixResult mwfResult = (WalkForwardMatrixResult)resultsGroup.mainResult().get("WalkForwardResult");
        if (mwfResult == null) {
            return false;
        }
        WalkForwardResult wfResult = mwfResult.getWFResult(resultkey, true);
        return wfResult != null;
    }

    private long parseLong(String str) {
        try {
            return Long.parseLong(str);
        }
        catch (Exception e) {
            return -1L;
        }
    }

    private long parseTime(String strDate) {
        try {
            return formaterDate.parseMillis(strDate);
        }
        catch (Exception e) {
            return Long.parseLong(strDate);
        }
    }
}

