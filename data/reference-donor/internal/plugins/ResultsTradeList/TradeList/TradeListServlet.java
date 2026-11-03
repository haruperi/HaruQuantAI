/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  com.strategyquant.tradinglib.stockchart.StockLoader
 *  com.strategyquant.tradinglib.stockchart.StockLoaderForStockPicking
 *  com.strategyquant.tradinglib.table.TradelistOrdersComparator
 *  com.strategyquant.tradinglib.tradelist.TradelistExport
 *  com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry
 *  com.strategyquant.tradinglib.tradelist.TradelistTableView
 *  com.strategyquant.tradinglib.tradelist.TradelistViewsManager
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.TradeList;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.results.SpecialValues;
import com.strategyquant.tradinglib.stockchart.StockLoader;
import com.strategyquant.tradinglib.stockchart.StockLoaderForStockPicking;
import com.strategyquant.tradinglib.table.TradelistOrdersComparator;
import com.strategyquant.tradinglib.tradelist.TradelistExport;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Comparator;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.StampedLock;
import java.util.jar.JarFile;
import java.util.zip.ZipFile;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradeListServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(TradeListServlet.class);
    private static final String LOCK_TRADELISTSERVLET = "TradeListServlet";
    private static final int MAX_CACHED_RESULTS = 50;
    private HashMap<String, ArrayList<Object[]>> dataCache = new HashMap();
    private HashMap<String, Long> lastUsed = new HashMap();
    private StampedLock lock = new StampedLock();
    private TradelistOrdersComparator comparator = new TradelistOrdersComparator();
    private static IResultsGroupProvider rgProvider;
    private DateTimeFormatter formaterFullDateTime = DateTimeFormat.forPattern((String)"yyyy-MM-dd HH:mm:ss");
    private boolean exportRunning = false;

    public TradeListServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        String[] urlArgs = command.split("/");
        if (urlArgs != null && urlArgs.length > 0) {
            switch (urlArgs[urlArgs.length - 1]) {
                case "getTrades": {
                    return this.onGetTrades(urlArgs, args);
                }
                case "export": {
                    return this.onExport(urlArgs, args);
                }
                case "exportCloud": {
                    return this.onExportCloud(urlArgs, args);
                }
            }
            return TradeListServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
        }
        return TradeListServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onGetTrades(String[] urlArgs, Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"resultKey", "direction", "sampleType"});
        JsonCreator responseJSON = new JsonCreator();
        Map params = this.getParameters(urlArgs, parameterMap);
        Map rgParams = this.getRgParams(params);
        boolean expired = false;
        try {
            expired = parameterMap.get("expired")[0].equals("true");
        }
        catch (Exception exception) {
            // empty catch block
        }
        params.put("expired", expired);
        ResultsGroup resultsGroup = rgProvider.get(rgParams, LOCK_TRADELISTSERVLET);
        try {
            if (resultsGroup.orders() == null) {
                responseJSON.put("total_count", (Object)0, true);
                responseJSON.beginObject();
                responseJSON.put("rows");
                responseJSON.beginArray();
                responseJSON.endArray(true);
                responseJSON.endObject(true);
                responseJSON.put("pos", (Object)0, false);
                String string = responseJSON.toString();
                return string;
            }
            TradelistTableView tradelistView = null;
            if (params.containsKey("viewXML")) {
                tradelistView = new TradelistTableView();
                tradelistView.setFromXML(XMLUtil.stringToElement((String)((String)params.get("viewXML"))));
            } else {
                tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
            }
            String identificator = this.getDataIdentificator(params, tradelistView, resultsGroup);
            boolean hasChartData = this.chartDataExists(resultsGroup, (String)params.get("resultKey"));
            this.loadTrades(params, resultsGroup, tradelistView, identificator, hasChartData, responseJSON);
        }
        catch (Exception e) {
            Log.error("Cannot load trades", (Throwable)e);
            String string = null;
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_TRADELISTSERVLET);
            }
        }
        if (Log.isDebugEnabled()) {
            Log.debug(responseJSON.toString());
        }
        return responseJSON.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onExport(String[] urlArgs, Map<String, String[]> parameterMap) throws Exception {
        this.checkParamExists(parameterMap, new String[]{"resultKey", "direction", "sampleType", "path", "useComma"});
        Map params = this.getParameters(urlArgs, parameterMap);
        if (this.exportRunning) {
            return TradeListServlet.apiErrorJSON((String)L.t((String)"Export is already running. Please wait until it finishes", (Object[])new Object[0]), null);
        }
        this.exportRunning = true;
        boolean expired = false;
        try {
            expired = parameterMap.get("expired")[0].equals("true");
        }
        catch (Exception exception) {
            // empty catch block
        }
        params.put("expired", expired);
        try {
            String path = parameterMap.get("path")[0];
            boolean useComma = Boolean.parseBoolean(parameterMap.get("useComma")[0]);
            Map rgParams = this.getRgParams(params);
            ResultsGroup resultsGroup = rgProvider.get(rgParams, LOCK_TRADELISTSERVLET);
            try {
                TradelistTableView tradelistView = null;
                if (params.containsKey("viewXML")) {
                    tradelistView = new TradelistTableView();
                    tradelistView.setFromXML(XMLUtil.stringToElement((String)((String)params.get("viewXML"))));
                } else {
                    tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
                }
                String identificator = this.getDataIdentificator(params, tradelistView, resultsGroup);
                String idBase = identificator.substring(0, identificator.lastIndexOf("#"));
                ArrayList<Object[]> rowData = this.generateNewData(resultsGroup, tradelistView, params, true);
                TradelistExport export = new TradelistExport();
                if (path.endsWith("xlsx")) {
                    export.toXlsx(rowData, path, useComma);
                } else {
                    export.toCsv(rowData, path, useComma);
                }
            }
            catch (Exception e) {
                Log.error("Cannot export trades", (Throwable)e);
                throw e;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(LOCK_TRADELISTSERVLET);
                }
            }
        }
        catch (Exception e) {
            String string = TradeListServlet.apiErrorJSON((String)L.t((String)"Tradelist export failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            this.exportRunning = false;
        }
        JSONObject responseJSON = new JSONObject();
        responseJSON.put("success", (Object)"Tradelist exported.");
        return responseJSON.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onExportCloud(String[] urlArgs, Map<String, String[]> parameterMap) throws Exception {
        JSONObject responseJSON = new JSONObject();
        this.checkParamExists(parameterMap, new String[]{"resultKey", "direction", "sampleType", "path", "useComma"});
        Map params = this.getParameters(urlArgs, parameterMap);
        if (this.exportRunning) {
            return TradeListServlet.apiErrorJSON((String)L.t((String)"Export is already running. Please wait until it finishes", (Object[])new Object[0]), null);
        }
        this.exportRunning = true;
        boolean expired = false;
        try {
            expired = parameterMap.get("expired")[0].equals("true");
        }
        catch (Exception exception) {
            // empty catch block
        }
        params.put("expired", expired);
        try {
            boolean useComma = Boolean.parseBoolean(parameterMap.get("useComma")[0]);
            String extension = parameterMap.get("extension")[0];
            Map rgParams = this.getRgParams(params);
            ResultsGroup resultsGroup = rgProvider.get(rgParams, LOCK_TRADELISTSERVLET);
            try {
                TradelistTableView tradelistView = null;
                if (params.containsKey("viewXML")) {
                    tradelistView = new TradelistTableView();
                    tradelistView.setFromXML(XMLUtil.stringToElement((String)((String)params.get("viewXML"))));
                } else {
                    tradelistView = TradelistViewsManager.getInstance().getSelectedTradelistView();
                }
                ArrayList<Object[]> rowData = this.generateNewData(resultsGroup, tradelistView, params, true);
                TradelistExport export = new TradelistExport();
                if (extension.equals("xlsx")) {
                    byte[] data = export.toXlsxCloud(rowData);
                    responseJSON.put("data", (Object)Base64.getEncoder().encodeToString(data));
                } else {
                    String csvContent = export.toCsvCloud(rowData, useComma);
                    responseJSON.put("data", (Object)Base64.getEncoder().encodeToString(csvContent.getBytes()));
                }
            }
            catch (Exception e) {
                Log.error("Cannot export trades", (Throwable)e);
                throw e;
            }
            finally {
                if (resultsGroup != null) {
                    resultsGroup.releaseLock(LOCK_TRADELISTSERVLET);
                }
            }
        }
        catch (Exception e) {
            String string = TradeListServlet.apiErrorJSON((String)L.t((String)"Tradelist export failed", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            this.exportRunning = false;
        }
        responseJSON.put("success", (Object)"Tradelist exported.");
        return responseJSON.toString();
    }

    private void loadTrades(Map<String, Object> params, ResultsGroup resultsGroup, TradelistTableView tradelistView, String identificator, boolean hasChartData, JsonCreator json) {
        json.beginObject();
        json.put("rows");
        json.beginArray();
        try {
            if (tradelistView == null) {
                Log.error("Cannot load the list of trades. No tradelist view is set.");
            }
            ArrayList<Object[]> rowData = null;
            if (this.dataCache.containsKey(identificator)) {
                rowData = this.dataCache.get(identificator);
            } else {
                rowData = this.generateNewData(resultsGroup, tradelistView, params, false);
                this.dataCache.put(identificator, rowData);
            }
            this.lastUsed.put(identificator, System.currentTimeMillis());
            int start = (Integer)params.get("posStart");
            int count = (Integer)params.get("count");
            for (int a = start; a < rowData.size() && a < start + count; ++a) {
                json.beginObject();
                json.put("data");
                json.beginArray();
                for (int i = 0; i < rowData.get(a).length - 5; ++i) {
                    Object value = rowData.get(a)[i];
                    json.setValue(value, true);
                }
                Byte orderType = (Byte)rowData.get(a)[rowData.get(a).length - 1];
                boolean isBuySell = orderType == 1 || orderType == 2;
                Byte sampleType = (Byte)rowData.get(a)[rowData.get(a).length - 2];
                if (sampleType >= 20 && sampleType <= 30) {
                    json.setValue((Object)2, true);
                } else if (sampleType >= 40 && sampleType <= 50) {
                    json.setValue((Object)1, true);
                } else {
                    json.setValue((Object)0, true);
                }
                if (isBuySell) {
                    json.setValue((Object)(hasChartData ? 1 : 2), true);
                } else {
                    json.setValue((Object)0, true);
                }
                json.setValue(rowData.get(a)[rowData.get(a).length - 5], true);
                json.setValue((Object)SQTime.toString((long)((Long)rowData.get(a)[rowData.get(a).length - 4]), (DateTimeFormatter)this.formaterFullDateTime), true);
                json.setValue((Object)SQTime.toString((long)((Long)rowData.get(a)[rowData.get(a).length - 3]), (DateTimeFormatter)this.formaterFullDateTime), false);
                json.endArray(true);
                json.put("id", (Object)("r" + (a + 1)), false);
                json.endObject(a < rowData.size() - 1 && a < start + count - 1);
            }
            json.endArray(true);
            json.put("total_count", (Object)rowData.size(), true);
            json.put("pos", (Object)start, false);
            json.endObject(false);
        }
        catch (Exception ex) {
            Log.error("Getting trades failed", (Throwable)ex);
        }
    }

    private ArrayList<Object[]> generateNewData(ResultsGroup resultsGroup, TradelistTableView tradelistView, Map<String, Object> params, boolean formated) throws Exception {
        if (this.dataCache.size() > 50) {
            this.deleteOldestData();
        }
        int sortColumn = (Integer)params.get("sortColumn");
        boolean asc = (Boolean)params.get("asc");
        String resultKey = (String)params.get("resultKey");
        OrdersList filteredOL = null;
        filteredOL = this.shouldShowControlOrders() ? resultsGroup.orders().filter(resultKey, ((Byte)params.get("direction")).byteValue(), ((Byte)params.get("sampleType")).byteValue(), (Boolean)params.get("expired") == false) : resultsGroup.orders().filterExcludingControlOrders(resultKey, ((Byte)params.get("direction")).byteValue(), ((Byte)params.get("sampleType")).byteValue(), (Boolean)params.get("expired") == false);
        if (resultsGroup.isPortfolio()) {
            if (!resultKey.equals("Portfolio")) {
                this.computeAccountBalance(filteredOL);
            } else {
                this.resetAccountBalance(filteredOL);
            }
        }
        if (sortColumn >= 0) {
            try {
                TradelistTableColumnEntry entry = (TradelistTableColumnEntry)tradelistView.columns.get(sortColumn);
                this.comparator.setColumn(entry.tableColumn);
                this.comparator.setAsc(asc);
                filteredOL.sort((Comparator)this.comparator);
            }
            catch (Exception e) {
                Log.error("Tradelist sorting failed", (Throwable)e);
            }
        }
        return tradelistView.getData(filteredOL, 0, filteredOL.size(), formated);
    }

    private void computeAccountBalance(OrdersList orders) {
        float balance = 0.0f;
        for (int i = 0; i < orders.size(); ++i) {
            Order o = orders.get(i);
            o.AccountBalanceTemp = balance += o.PL;
        }
    }

    private void resetAccountBalance(OrdersList orders) {
        for (int i = 0; i < orders.size(); ++i) {
            Order o = orders.get(i);
            o.AccountBalanceTemp = -1.0E8f;
        }
    }

    private void deleteOldestData() {
        String oldestID = null;
        long oldestTime = Long.MAX_VALUE;
        for (String id : this.lastUsed.keySet()) {
            long lastTimeUsed = this.lastUsed.get(id);
            if (lastTimeUsed >= oldestTime) continue;
            oldestTime = lastTimeUsed;
            oldestID = id;
        }
        this.dataCache.remove(oldestID);
        this.lastUsed.remove(oldestID);
    }

    private String getDataIdentificator(Map<String, Object> params, TradelistTableView view, ResultsGroup rg) {
        StringBuilder builder = new StringBuilder();
        builder.append(params.get("projectName"));
        builder.append(params.get("databankName"));
        builder.append(params.containsKey("backtestID") ? params.get("backtestID") : params.get("strategyName"));
        builder.append(view.name);
        builder.append(view.lastChanged);
        builder.append(params.get("resultKey"));
        builder.append(params.get("direction"));
        builder.append(params.get("sampleType"));
        builder.append(params.get("sortColumn"));
        builder.append(params.get("asc"));
        builder.append(params.get("expired"));
        builder.append(this.shouldShowControlOrders());
        builder.append("#");
        builder.append(rg.specialValues().getLong(SpecialValues.LastModified));
        return builder.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private boolean chartDataExists(ResultsGroup rg, String resultKey) {
        ZipFile file = null;
        try {
            StockLoaderForStockPicking loader;
            resultKey = resultKey.replace("amp", "&");
            Result result = rg.subResult(resultKey);
            file = new JarFile(result.getStockChartPath());
            if (rg.isStockpickerStrategy()) {
                loader = new StockLoaderForStockPicking();
                loader.load((JarFile)file, null, null, null, false, false, result.getResultKey(), null, null);
            } else {
                loader = new StockLoader();
                loader.load((JarFile)file, null, null, null, true, false, result.getResultKey(), null);
            }
            boolean bl = true;
            return bl;
        }
        catch (Exception e) {
            boolean bl = false;
            return bl;
        }
        finally {
            if (file != null) {
                try {
                    file.close();
                }
                catch (Exception exception) {}
            }
        }
    }

    private boolean shouldShowControlOrders() {
        boolean showControlOrders = false;
        try {
            showControlOrders = Boolean.parseBoolean(MainApp.settings().get("showControlOrders", "false"));
        }
        catch (Exception exception) {
            // empty catch block
        }
        return showControlOrders;
    }
}

