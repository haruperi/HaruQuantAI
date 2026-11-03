/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.SymbolData
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DukasDataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.qdm.QDM
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.dukascopy.CdnInfo
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.apache.http.client.ClientProtocolException
 *  org.apache.http.client.methods.CloseableHttpResponse
 *  org.apache.http.client.methods.HttpGet
 *  org.apache.http.client.methods.HttpUriRequest
 *  org.apache.http.impl.client.HttpClientBuilder
 *  org.jdom2.Document
 *  org.jdom2.Element
 *  org.jdom2.JDOMException
 *  org.jdom2.input.SAXBuilder
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Dukascopy;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.SymbolData;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DukasDataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.qdm.QDM;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.dukascopy.CdnInfo;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.IOException;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import org.apache.http.client.ClientProtocolException;
import org.apache.http.client.methods.CloseableHttpResponse;
import org.apache.http.client.methods.HttpGet;
import org.apache.http.client.methods.HttpUriRequest;
import org.apache.http.impl.client.HttpClientBuilder;
import org.jdom2.Document;
import org.jdom2.Element;
import org.jdom2.JDOMException;
import org.jdom2.input.SAXBuilder;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DukasServlet
extends HttpJSONServlet {
    DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyyMMdd");
    private static final Logger Log = LoggerFactory.getLogger(DukasServlet.class);
    private boolean canceled = false;
    private String availableDataResponse = null;

    public DukasServlet() {
        this.preloadAvailableDataResponse();
    }

    private void preloadAvailableDataResponse() {
        if (!MainApp.runInConsole()) {
            new Thread(){

                @Override
                public void run() {
                    try {
                        DukasServlet.this.availableDataResponse = DukasServlet.this.onGetDataList();
                    }
                    catch (Exception ex) {
                        Log.error("Cannot load Dukas data.", (Throwable)ex);
                    }
                }
            }.start();
        }
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getDataList": {
                return this.onGetDataList();
            }
            case "addData": {
                return this.onAddData(args);
            }
            case "addCancel": {
                return this.onAddCancel();
            }
            case "importData": {
                return this.onImportData(args);
            }
            case "importDataAction": {
                return this.onImportDataAction(args);
            }
            case "setParallelDownload": {
                return this.onSetParallelDownload(args);
            }
            case "getParallelDownload": {
                return this.onGetParallelDownload();
            }
            case "updateAll": {
                return this.onUpdateAll();
            }
            case "updateSelected": {
                return this.onUpdateSelected(args);
            }
        }
        return DukasServlet.apiErrorJSON((String)L.t((String)"Execution failed. Unknown command '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onGetParallelDownload() {
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        response.put("parallelDownload", (Object)MainApp.settings().get("parallelDownload", "3"));
        response.put("cdnParallelDownload", (Object)MainApp.settings().get("cdnParallelDownload", "3"));
        response.put("cdnPreferred", (Object)MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN));
        return response.toString();
    }

    private String onSetParallelDownload(Map<String, String[]> args) throws Exception {
        String download = this.tryGetParam(args, "parallelDownload")[0];
        String cdnDownload = this.tryGetParam(args, "cdnParallelDownload")[0];
        String cdnPreferred = this.tryGetParam(args, "cdnPreferred")[0];
        DownloadDispatcher.get().setQueueSizes(Integer.valueOf(download).intValue(), Integer.valueOf(cdnDownload).intValue());
        MainApp.settings().set("parallelDownload", download);
        MainApp.settings().set("cdnParallelDownload", cdnDownload);
        MainApp.settings().set("cdnPreferred", cdnPreferred);
        MainApp.settings().save();
        JSONObject response = new JSONObject();
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onGetDataList() {
        if (this.availableDataResponse != null) {
            return this.availableDataResponse;
        }
        JSONObject response = new JSONObject();
        JSONArray dataArray = new JSONArray();
        ArrayList<String> categories = new ArrayList<String>();
        JSONArray categoriesJSON = new JSONArray();
        categoriesJSON.put((Object)new JSONObject().put("name", (Object)"All").put("value", (Object)""));
        for (SymbolData data : DukasDataManager.get().getAvailableDataList()) {
            JSONObject dataObj = new JSONObject();
            dataObj.put("symbol", (Object)data.symbol);
            dataObj.put("name", (Object)data.name);
            String fullCategory = data.category + " - " + data.subcategory;
            dataObj.put("category", (Object)data.category);
            dataObj.put("subCategory", (Object)data.subcategory);
            dataObj.put("fullCategory", (Object)fullCategory);
            dataObj.put("dateFrom", data.dateFrom);
            dataObj.put("dateFromM1", data.dateFromM1);
            dataObj.put("decimals", data.decimals);
            dataObj.put("tickValue", data.tickValue);
            dataObj.put("defaultSpread", data.defaultSpread);
            dataObj.put("tickSize", data.tickSize);
            dataObj.put("tickStep", data.tickStep);
            dataObj.put("instrumentType", (int)data.instrumentType);
            dataArray.put((Object)dataObj);
            if (!categories.contains(data.category)) {
                categories.add(data.category);
                categoriesJSON.put((Object)new JSONObject().put("name", (Object)(data.category + " - All")).put("value", (Object)data.category));
            }
            if (categories.contains(fullCategory)) continue;
            categories.add(fullCategory);
            categoriesJSON.put((Object)new JSONObject().put("name", (Object)fullCategory).put("value", (Object)fullCategory));
        }
        response.put("categories", (Object)categoriesJSON);
        response.put("data", (Object)dataArray);
        response.put("success", (Object)L.t((String)"Data listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAddData(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols[]"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onAdd(args);
        } else {
            new Thread(this){
                final /* synthetic */ DukasServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    this.this$0._onAdd(args);
                }
            }.start();
        }
        response.put("success", (Object)L.t((String)"Add symbols.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _onAdd(Map<String, String[]> args) {
        JSONObject progress = new JSONObject();
        String error = null;
        try {
            CharSequence[] symbols = this.tryGetParam(args, "symbols[]");
            String[] instruments = args.containsKey("instruments[]") ? this.tryGetParam(args, "instruments[]") : null;
            String postfix = args.containsKey("postfix") ? this.tryGetParamValue(args, "postfix") : "";
            String timeframe = this.tryGetParam(args, "dataType")[0];
            int broker = Integer.valueOf(this.tryGetParamValue(args, "broker"));
            if (!timeframe.equals("TICK") && !timeframe.equals("M1")) {
                throw new Exception(L.t((String)"Invalid data type. Must be %s or %s", (Object[])new Object[]{"TICK", "M1"}));
            }
            int percent = 0;
            for (int i = 0; i < symbols.length; ++i) {
                String instrument;
                String symbol = symbols[i];
                String string = instrument = instruments == null ? null : instruments[i];
                if (instrument != null && instrument.equals("-1")) {
                    instrument = null;
                }
                String symbolAdded = DukasDataManager.get().addData(symbol, postfix, broker, instrument);
                DataManager.updateTimeframe((String)"History", (String)symbolAdded, (String)timeframe);
                Log.info(String.format("Symbol '%s' added.", symbolAdded));
                percent = SQUtils.round((double)(100.0 * (double)i / (double)symbols.length));
                progress.put("percent", percent);
                progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbolAdded}));
                DataManagerAddProgressSender.getInstance().sendData(progress);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)String.join((CharSequence)",", symbols), (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                if (!this.canceled) continue;
                break;
            }
        }
        catch (Exception e) {
            Log.error("Cannot add symbols. Exc.", (Throwable)e);
            error = e.getMessage();
        }
        finally {
            progress.put("percent", 100);
            progress.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
            if (error != null) {
                progress.put("error", (Object)error);
            }
            DataManagerAddProgressSender.getInstance().sendData(progress);
        }
    }

    private String onAddCancel() throws Exception {
        JSONObject response = new JSONObject();
        this.canceled = true;
        response.put("success", (Object)L.t((String)"Adding symbols canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateAll() {
        try {
            ArrayList allSymbols = DataManager.list();
            ArrayList<DataInfo> dukasSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < allSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)allSymbols.get(i);
                if (dataInfo.source != 2 || dataInfo.sourceDataId != 0) continue;
                dukasSymbols.add((DataInfo)allSymbols.get(i));
            }
            if (dukasSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            CharSequence[] symbols = new String[dukasSymbols.size()];
            CharSequence[] uSymbols = new String[dukasSymbols.size()];
            for (int i = 0; i < dukasSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)dukasSymbols.get(i);
                symbols[i] = dataInfo.symbol;
                uSymbols[i] = dataInfo.uSymbol;
            }
            args.put("symbols", new String[]{String.join((CharSequence)",", symbols)});
            args.put("uSymbols", new String[]{String.join((CharSequence)",", uSymbols)});
            args.put("dateFrom", new String[]{"2013.01.01"});
            args.put("dateTo", new String[]{SQTime.toUIDateString((long)System.currentTimeMillis())});
            args.put("dateType", new String[]{"sinceLast"});
            args.put("overwrite", new String[]{"true"});
            args.put("dataType", new String[]{"M1"});
            String cnd = MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN);
            args.put("downloadType", new String[]{cnd});
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DukasServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onUpdateSelected(Map<String, String[]> map) {
        try {
            DataInfo dataInfo;
            CharSequence[] symbols = this.tryGetParam(map, "symbols")[0].split(",");
            String[] datesFrom = null;
            try {
                datesFrom = this.tryGetParam(map, "datesFrom")[0].split(",");
            }
            catch (Exception exception) {
                // empty catch block
            }
            String[] datesTo = null;
            try {
                datesTo = this.tryGetParam(map, "datesTo")[0].split(",");
            }
            catch (Exception exception) {
                // empty catch block
            }
            ArrayList<DataInfo> dukasSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < symbols.length; ++i) {
                dataInfo = DataManager.getDataInfo((String)"History", (String)symbols[i]);
                if (dataInfo.source != 2 || dataInfo.sourceDataId != 0) continue;
                dataInfo.dateFromStr = datesFrom == null ? null : datesFrom[i];
                dataInfo.dateToStr = datesTo == null ? null : datesTo[i];
                dukasSymbols.add(dataInfo);
            }
            if (dukasSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            symbols = new String[dukasSymbols.size()];
            CharSequence[] uSymbols = new String[dukasSymbols.size()];
            CharSequence[] uDatesFrom = new String[dukasSymbols.size()];
            CharSequence[] uDatesTo = new String[dukasSymbols.size()];
            for (int i = 0; i < dukasSymbols.size(); ++i) {
                dataInfo = (DataInfo)dukasSymbols.get(i);
                symbols[i] = dataInfo.symbol;
                uSymbols[i] = dataInfo.uSymbol;
                uDatesFrom[i] = dataInfo.dateFromStr;
                uDatesTo[i] = dataInfo.dateToStr;
            }
            args.put("symbols", new String[]{String.join((CharSequence)",", symbols)});
            args.put("uSymbols", new String[]{String.join((CharSequence)",", uSymbols)});
            args.put("dateFrom", new String[]{"2013.01.01"});
            args.put("dateTo", new String[]{SQTime.toUIDateString((long)System.currentTimeMillis())});
            args.put("dateType", new String[]{"sinceLast"});
            args.put("overwrite", new String[]{"true"});
            args.put("dataType", new String[]{"M1"});
            String cnd = MainApp.settings().get("cdnPreferred", DataSources.DOWNLOAD_TYPE_CDN);
            args.put("downloadType", new String[]{cnd});
            if (datesFrom != null && datesTo != null) {
                args.put("datesFrom", new String[]{String.join((CharSequence)",", uDatesFrom)});
                args.put("datesTo", new String[]{String.join((CharSequence)",", uDatesTo)});
            }
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DukasServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }

    private String onImportData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
            String[] uSymbols = this.tryGetParam(args, "uSymbols")[0].split(",");
            long dateFrom = SQTime.parseToMilis((String)this.tryGetParam(args, "dateFrom")[0], (String)"yyyy.MM.dd");
            long dateTo = SQTime.parseToMilis((String)this.tryGetParam(args, "dateTo")[0], (String)"yyyy.MM.dd");
            String dateType = this.tryGetParam(args, "dateType")[0];
            boolean overwrite = this.tryGetParam(args, "overwrite")[0].equals("true");
            String[] datesFrom = null;
            try {
                datesFrom = this.tryGetParam(args, "datesFrom")[0].split(",");
            }
            catch (Exception exception) {
                // empty catch block
            }
            String[] datesTo = null;
            try {
                datesTo = this.tryGetParam(args, "datesTo")[0].split(",");
            }
            catch (Exception exception) {
                // empty catch block
            }
            String downloadType = this.getParam(args, "downloadType", DataSources.DOWNLOAD_TYPE_CDN);
            int parallelDownload = Integer.parseInt(MainApp.settings().get("parallelDownload", "3"));
            int cdnParallelDownload = Integer.parseInt(MainApp.settings().get("cdnParallelDownload", "3"));
            DownloadDispatcher.get().setQueueSizes(parallelDownload, cdnParallelDownload);
            for (int a = 0; a < symbols.length; ++a) {
                String symbol = symbols[a];
                DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
                if (info.source != 2) continue;
                if (datesFrom != null && datesTo != null) {
                    dateFrom = SQTime.parseToMilis((String)datesFrom[a], (String)"yyyy.MM.dd");
                    dateTo = SQTime.parseToMilis((String)datesTo[a], (String)"yyyy.MM.dd");
                }
                ImportInfo importInfo = new ImportInfo();
                importInfo.origSymbol = uSymbols[a];
                importInfo.symbol = symbol;
                importInfo.overwrite = overwrite;
                importInfo.downloadType = downloadType;
                importInfo.useCDN = true;
                importInfo.instrumentInfo = info.symbolInfo;
                importInfo.rows = info.rows;
                importInfo.oldDateFrom = info.dateFrom;
                importInfo.oldDateTo = info.dateTo;
                importInfo.ignoreWeekend = info.symbolInfo.dataType == 3;
                boolean downloadM1Data = info.timeframe != null && info.timeframe.equals("M1");
                SymbolData symbolData = DukasDataManager.get().getAvailableDataInfo(importInfo.origSymbol);
                if (symbolData == null) {
                    throw new Exception(L.t((String)"No info found for symbol '%s'.", (Object[])new Object[]{importInfo.origSymbol}));
                }
                importInfo.priceConstant = Math.pow(10.0, -symbolData.decimals);
                importInfo.downloadM1Data = downloadM1Data;
                importInfo.dateFrom = dateFrom;
                importInfo.dateTo = dateTo;
                if (dateType.equals("allTime")) {
                    importInfo.dateFrom = downloadM1Data ? symbolData.dateFromM1 : symbolData.dateFrom;
                } else if (dateType.equals("sinceLast")) {
                    long l = info.dateTo > 0L ? info.dateTo : (importInfo.dateFrom = downloadM1Data ? symbolData.dateFromM1 : symbolData.dateFrom);
                }
                if (importInfo.dateFrom > importInfo.dateTo) {
                    return DukasServlet.apiErrorJSON((String)L.t((String)"Date from must be before Date to.", (Object[])new Object[0]), null);
                }
                this.sanitizeDates(importInfo, downloadM1Data, symbolData);
                if (downloadM1Data) {
                    QDM.getInstance().activity.increase(importInfo.useCDN ? 4 : 2);
                } else {
                    QDM.getInstance().activity.increase(importInfo.useCDN ? 3 : 1);
                }
                DownloadDispatcher.get().update(info, importInfo);
            }
        }
        catch (Exception e) {
            return DukasServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
    }

    private void sanitizeDates(ImportInfo importInfo, boolean downloadM1Data, SymbolData symbolData) {
        if (downloadM1Data) {
            if (importInfo.dateFrom < symbolData.dateFromM1) {
                importInfo.dateFrom = symbolData.dateFromM1;
            }
        } else if (importInfo.dateFrom < symbolData.dateFrom) {
            importInfo.dateFrom = symbolData.dateFrom;
        }
    }

    private void fillCdnInfos(CdnInfo cdnInfo, String cdnDescUrl) throws ClientProtocolException, IOException, IllegalStateException, JDOMException {
        CloseableHttpResponse response = HttpClientBuilder.create().build().execute((HttpUriRequest)new HttpGet(cdnDescUrl));
        response.getEntity().getContent();
        SAXBuilder builder = new SAXBuilder();
        Document document = builder.build(response.getEntity().getContent());
        Element datasEl = document.getRootElement();
        List dataEls = datasEl.getChildren("data");
        for (Element dataEl : dataEls) {
            String symbol = dataEl.getAttributeValue("symbol");
            String url = dataEl.getAttributeValue("url");
            String format = dataEl.getAttributeValue("format");
            String tf = dataEl.getAttributeValue("tf");
            cdnInfo.addSymbolInfo(symbol, tf, url, format);
            Log.debug("CDN metadata added:" + symbol + ", timeframe:" + tf + ", url:" + url);
        }
    }

    private String onImportDataAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        MultiProgressListener listener = DataManagerDataProgress.get().createListener(symbol);
        switch (action) {
            case "stop": {
                DownloadDispatcher.get().stop(symbol);
                break;
            }
            case "pause": {
                listener.onPause();
                DownloadDispatcher.get().pause(symbol);
                break;
            }
            case "continue": {
                listener.onContinue();
                DownloadDispatcher.get().resume(symbol);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

