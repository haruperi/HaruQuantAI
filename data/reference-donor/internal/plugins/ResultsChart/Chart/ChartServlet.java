/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.Result
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.stockchart.StockData
 *  com.strategyquant.tradinglib.stockchart.StockLoader
 *  com.strategyquant.tradinglib.stockchart.StockLoaderForStockPicking
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.Chart;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.Result;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.stockchart.StockData;
import com.strategyquant.tradinglib.stockchart.StockLoader;
import com.strategyquant.tradinglib.stockchart.StockLoaderForStockPicking;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.Map;
import java.util.jar.JarFile;
import java.util.zip.ZipFile;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ChartServlet
extends HttpJSONServlet {
    private static final DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyy-MM-dd HH:mm:ss");
    private static final Logger Log = LoggerFactory.getLogger(ChartServlet.class);
    private static final String LOCK_CHARTSERVLET = "ChartServlet";
    private static IResultsGroupProvider rgProvider;

    public ChartServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) {
        switch (command) {
            case "loadChartData": {
                return this.onLoadChartData(args);
            }
        }
        return ChartServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private Long tryToParseTime(String str) {
        try {
            return formaterDate.parseMillis(str);
        }
        catch (Exception e) {
            return null;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onLoadChartData(Map<String, String[]> parameterMap) {
        ZipFile file = null;
        String chartJson = null;
        try {
            StockLoaderForStockPicking loader;
            String symbol;
            DataInfo dataInfo;
            Long from = null;
            boolean isDate = false;
            try {
                String strFrom = this.tryGetParam(parameterMap, "indexFrom")[0];
                from = this.tryToParseTime(strFrom);
                if (from == null) {
                    from = (long)Double.parseDouble(strFrom);
                } else {
                    isDate = true;
                }
            }
            catch (Exception strFrom) {
                // empty catch block
            }
            Long to = null;
            try {
                String strTo = this.tryGetParam(parameterMap, "indexTo")[0];
                to = this.tryToParseTime(strTo);
                if (to == null) {
                    to = (long)Double.parseDouble(strTo);
                } else {
                    isDate = true;
                }
            }
            catch (Exception strTo) {
                // empty catch block
            }
            boolean savePreview = true;
            try {
                savePreview = !this.tryGetParam(parameterMap, "preview")[0].equalsIgnoreCase("false");
            }
            catch (Exception exception) {
                // empty catch block
            }
            Long tradeId = null;
            try {
                String tradeIdStr = this.tryGetParam(parameterMap, "trade")[0];
                tradeId = Long.parseLong(tradeIdStr);
            }
            catch (Exception tradeIdStr) {
                // empty catch block
            }
            Integer zoomWidth = null;
            try {
                String zoomWidthStr = this.tryGetParam(parameterMap, "zoomWidth")[0];
                zoomWidth = Integer.parseInt(zoomWidthStr);
            }
            catch (Exception zoomWidthStr) {
                // empty catch block
            }
            ResultsGroup rg = rgProvider.get(parameterMap, LOCK_CHARTSERVLET);
            String resultKey = rg.getMainResultKey();
            Double pipValue = null;
            ArrayList symbols = rg.symbols().list();
            if (symbols != null && !symbols.isEmpty() && (dataInfo = DataManager.getDataInfo((String)"History", (String)(symbol = (String)symbols.get(0)))) != null) {
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument);
                pipValue = instrumentInfo.tickSize;
            }
            boolean stockPicker = false;
            try {
                String path;
                Result result = rg.subResult(resultKey);
                Databank db = rg.getDatabank();
                stockPicker = rg.isStockpickerStrategy();
                String string = path = db != null && db.isFileBased() && rg.storesChartData() ? rg.getFilePath() : result.getStockChartPath();
                if (path == null) {
                    String string2 = ChartServlet.apiErrorJSON((String)L.t((String)"Cannot load charts.", (Object[])new Object[0]), null);
                    return string2;
                }
                Log.info("Using chart path {}", (Object)path);
                file = new JarFile(path);
            }
            finally {
                rg.releaseLock(LOCK_CHARTSERVLET);
            }
            StockData chartData = null;
            if (stockPicker) {
                loader = new StockLoaderForStockPicking();
                String[] stocks = parameterMap.get("stock");
                String stock = stocks == null ? null : stocks[0];
                chartData = loader.load((JarFile)file, from, to, tradeId, savePreview, isDate, resultKey, zoomWidth, stock);
            } else {
                loader = new StockLoader();
                chartData = loader.load((JarFile)file, from, to, tradeId, savePreview, isDate, resultKey, zoomWidth);
            }
            chartData.setPipValue(pipValue);
            chartJson = chartData.toJSON();
        }
        catch (Exception e) {
            Log.error("Error while loading chart", (Throwable)e);
            String string = ChartServlet.apiErrorJSON((String)L.t((String)"Cannot load charts.", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            if (file != null) {
                try {
                    file.close();
                }
                catch (Exception exception) {}
            }
        }
        JsonCreator jsonCreator = new JsonCreator();
        jsonCreator.beginObject();
        jsonCreator.put("success", (Object)"Charts data loaded", true);
        jsonCreator.putRaw("chart", (Object)chartJson, false);
        try {
            jsonCreator.separator();
            jsonCreator.put("requestId", (Object)this.tryGetParam(parameterMap, "requestId")[0], false);
        }
        catch (Exception exception) {
            // empty catch block
        }
        jsonCreator.endObject(false);
        return jsonCreator.toJson();
    }
}

