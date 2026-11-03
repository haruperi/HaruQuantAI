/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.pluginlib.ISQPlugin
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.exchange.IExchange
 *  com.strategyquant.tradinglib.exchange.SymbolInfo
 *  com.strategyquant.tradinglib.project.console.CLILogger
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Crypto;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.exchange.SymbolInfo;
import com.strategyquant.tradinglib.project.console.CLILogger;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataSourceCryptoServlet
extends HttpJSONServlet {
    public static final String DOWNLOAD_JOB = "DownloadCryptoSymbolJob_";
    private static final Logger Log = LoggerFactory.getLogger(DataSourceCryptoServlet.class);
    private boolean canceled = false;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getExchanges": {
                return this.onGetExchanges(args);
            }
            case "getSymbols": {
                return this.onGetSymbols(args);
            }
            case "add": {
                return this.onAdd(args);
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
            case "updateAll": {
                return this.onUpdateAll();
            }
            case "updateSelected": {
                return this.onUpdateSelected(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onGetExchanges(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        JSONArray exchanges = new JSONArray();
        for (IExchange plugin : SQPluginManager.getPlugins(IExchange.class)) {
            JSONObject exchange = new JSONObject();
            exchange.put("name", (Object)plugin.getName());
            exchange.put("value", (Object)SQPluginManager.getPluginName((ISQPlugin)plugin));
            exchanges.put((Object)exchange);
        }
        response.put("exchanges", (Object)exchanges);
        response.put("success", (Object)L.t((String)"Exchanges listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onGetSymbols(Map<String, String[]> args) throws Exception {
        String exchange = this.tryGetParam(args, "exchange")[0];
        IExchange plugin = (IExchange)SQPluginManager.findPluginByName((String)exchange);
        if (plugin == null) {
            throw new Exception(L.t((String)"Cannot find plugin for '%s'.", (Object[])new Object[]{exchange}));
        }
        JSONObject response = new JSONObject();
        response.put("symbols", (Object)plugin.getSymbols());
        response.put("timeframes", (Object)plugin.availableTimeframes());
        response.put("success", (Object)L.t((String)"Symbols listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onAdd(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onAdd(args);
        } else {
            new Thread(this){
                final /* synthetic */ DataSourceCryptoServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    this.this$0._onAdd(args);
                }
            }.start();
            response.put("success", (Object)L.t((String)"Add symbols.", (Object[])new Object[0]));
        }
        return response.toString();
    }

    private String onAddCancel() throws Exception {
        JSONObject response = new JSONObject();
        this.canceled = true;
        response.put("success", (Object)L.t((String)"Adding symbols canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _onAdd(Map<String, String[]> args) {
        JSONObject progress = new JSONObject();
        String error = null;
        LinkedList<String> errorSymbols = new LinkedList<String>();
        int added = 0;
        try {
            String exchange = this.tryGetParam(args, "exchange")[0];
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
            String timeframe = this.tryGetParam(args, "timeframe")[0];
            String postfix = args.containsKey("postfix") ? this.tryGetParamValue(args, "postfix") : "";
            IExchange plugin = (IExchange)SQPluginManager.findPluginByName((String)exchange);
            if (plugin == null) {
                throw new Exception(L.t((String)"Cannot find plugin for '%s'.", (Object[])new Object[]{exchange}));
            }
            Log.info(String.format("Checking timeframe '%s'.", timeframe));
            boolean timeframeSupported = false;
            JSONArray timeframes = plugin.availableTimeframes();
            for (int i = 0; i < timeframes.length(); ++i) {
                if (!timeframe.equals(timeframes.getString(i))) continue;
                timeframeSupported = true;
                break;
            }
            if (!timeframeSupported) {
                throw new Exception(L.t((String)"Timeframe '%s' not supported.", (Object[])new Object[]{timeframe}));
            }
            int percent = 0;
            for (int i = 0; i < symbols.length; ++i) {
                String symbol = symbols[i];
                Log.info(String.format("Checking symbol '%s'.", symbol));
                if (i > 0) {
                    Thread.sleep(500L);
                }
                if (!plugin.checkSymbolExists(symbol)) {
                    Log.error("Unknown symbol '" + symbol + "'. It wasn't possible to check selected symbol on crypto exchange.");
                    errorSymbols.add(symbol);
                    continue;
                }
                try {
                    String symbolAdded = this.addData(symbol, postfix, plugin);
                    DataManager.updateTimeframe((String)"History", (String)symbolAdded, (String)timeframe);
                    Log.info(L.t((String)"Symbol '%s' added.", (Object[])new Object[]{symbolAdded}));
                    percent = SQUtils.round((double)(100.0 * (double)i / (double)symbols.length));
                    progress.put("percent", percent);
                    progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbolAdded}));
                    DataManagerAddProgressSender.getInstance().sendData(progress);
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbol, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    ++added;
                }
                catch (Exception e) {
                    Log.error("Error while adding symbol " + symbol, (Throwable)e);
                    errorSymbols.add(symbol);
                }
                if (!this.canceled) continue;
                break;
            }
        }
        catch (Exception e) {
            Log.error("Cannot add symbols. Exc.", (Throwable)e);
            error = e.getMessage();
            if (MainApp.runInConsoleWithoutActiveWebserver()) {
                CLILogger.log((String)("Cannot add symbols. " + error));
            }
        }
        finally {
            progress.put("percent", 100);
            progress.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
            if (!errorSymbols.isEmpty()) {
                progress.put("error", (Object)("Error while adding symbols: " + String.join((CharSequence)", ", errorSymbols)));
            }
            if (error != null) {
                progress.put("error", (Object)error);
            }
            DataManagerAddProgressSender.getInstance().sendData(progress);
        }
    }

    private String addData(String symbol, String postfix, IExchange plugin) throws Exception {
        String exchange = plugin.getName();
        SymbolInfo symbolInfo = plugin.getSymbolInfo(symbol);
        double pointValue = symbolInfo.getPointValue();
        double tickSize = symbolInfo.getTickSize();
        double tickStep = symbolInfo.getTickStep();
        double defaultSpread = symbolInfo.getDefaultSpread();
        double defaultSlippage = symbolInfo.getDefaultSlippage();
        String symbolName = symbol + postfix;
        String instrumentName = symbol;
        while (DataManager.checkDataExists((String)"History", (String)symbolName)) {
            symbolName = DataManager.generateName((String)symbolName);
        }
        if (!InstrumentManager.checkInstrumentExists((String)instrumentName)) {
            InstrumentManager.addInstrument((String)instrumentName, (String)"Crypto instrument", (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)7, null, null, null, null, (double)1.0, (double)0.0);
        } else {
            InstrumentInfo instrument = InstrumentManager.getInstrumentInfo((String)instrumentName);
            if (instrument.tickSize != tickSize || instrument.tickStep != tickStep) {
                while (InstrumentManager.checkInstrumentExists((String)instrumentName)) {
                    instrumentName = DataManager.generateName((String)instrumentName);
                }
                InstrumentManager.addInstrument((String)instrumentName, (String)"Crypto instrument", (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)7, null, null, null, null, (double)1.0, (double)0.0);
            }
        }
        DataManager.addData((String)"History", (String)symbolName, (String)instrumentName, (int)1, (int)7, (String)symbol, (String)exchange);
        return symbolName;
    }

    private String onImportData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
            String[] uSymbols = this.tryGetParam(args, "uSymbols")[0].split(",");
            String dateType = this.tryGetParam(args, "dateType")[0];
            long dateFrom = 0L;
            try {
                dateFrom = SQTime.parseToMilis((String)this.tryGetParam(args, "dateFrom")[0], (String)"yyyy.MM.dd");
            }
            catch (Exception exception) {
                // empty catch block
            }
            long dateTo = System.currentTimeMillis();
            try {
                dateTo = SQTime.parseToMilis((String)this.tryGetParam(args, "dateTo")[0], (String)"yyyy.MM.dd");
            }
            catch (Exception exception) {
                // empty catch block
            }
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
            for (int a = 0; a < symbols.length; ++a) {
                String symbol = symbols[a];
                if (datesFrom != null && datesTo != null) {
                    dateFrom = SQTime.parseToMilis((String)datesFrom[a], (String)"yyyy.MM.dd");
                    dateTo = SQTime.parseToMilis((String)datesTo[a], (String)"yyyy.MM.dd");
                }
                ImportInfo importInfo = new ImportInfo();
                importInfo.origSymbol = uSymbols[a];
                importInfo.symbol = symbol;
                importInfo.overwrite = overwrite;
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
                if (dataInfo == null) {
                    throw new Exception(L.t((String)"Symbol with name '%s' doesn't exist.", (Object[])new Object[]{symbol}));
                }
                importInfo.instrumentInfo = dataInfo.symbolInfo;
                importInfo.rows = dataInfo.rows;
                importInfo.oldDateFrom = dataInfo.dateFrom;
                importInfo.oldDateTo = dataInfo.dateTo;
                importInfo.dateFrom = dateFrom;
                importInfo.dateTo = dateTo;
                if (dateType.equals("allTime")) {
                    importInfo.dateFrom = 0L;
                } else if (dateType.equals("sinceLast")) {
                    importInfo.dateFrom = dataInfo.dateTo > 0L ? SQTime.correctDayStart((long)dataInfo.dateTo) : 0L;
                } else {
                    importInfo.dateFrom = SQTime.correctDayStart((long)importInfo.dateFrom);
                    importInfo.dateTo = SQTime.correctDayEnd((long)importInfo.dateTo);
                }
                if (SQTime.getDateInMs((long)importInfo.dateTo) == SQTime.getDateInMs((long)System.currentTimeMillis())) {
                    importInfo.dateTo = SQTime.minus((long)importInfo.dateTo, (int)5, (int)1);
                }
                if (importInfo.dateFrom > importInfo.dateTo) {
                    return DataSourceCryptoServlet.apiErrorJSON((String)L.t((String)"Date from must be before Date to.", (Object[])new Object[0]), null);
                }
                DownloadDispatcher.get().update(dataInfo, importInfo);
            }
        }
        catch (Exception e) {
            return DataSourceCryptoServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
    }

    private String getJobId(String symbol) {
        return DOWNLOAD_JOB + symbol;
    }

    private String onUpdateAll() {
        try {
            ArrayList allSymbols = DataManager.list();
            ArrayList<DataInfo> cryptoSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < allSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)allSymbols.get(i);
                if (dataInfo.source != 7 || dataInfo.sourceDataId != 0) continue;
                cryptoSymbols.add((DataInfo)allSymbols.get(i));
            }
            if (cryptoSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            CharSequence[] symbols = new String[cryptoSymbols.size()];
            CharSequence[] uSymbols = new String[cryptoSymbols.size()];
            for (int i = 0; i < cryptoSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)cryptoSymbols.get(i);
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
            args.put("useCDN", new String[]{"true"});
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DataSourceCryptoServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
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
            ArrayList<DataInfo> cryptoSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < symbols.length; ++i) {
                dataInfo = DataManager.getDataInfo((String)"History", (String)symbols[i]);
                if (dataInfo.source != 7 || dataInfo.sourceDataId != 0) continue;
                dataInfo.dateFromStr = datesFrom == null ? null : datesFrom[i];
                dataInfo.dateToStr = datesTo == null ? null : datesTo[i];
                cryptoSymbols.add(dataInfo);
            }
            if (cryptoSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            symbols = new String[cryptoSymbols.size()];
            CharSequence[] uSymbols = new String[cryptoSymbols.size()];
            CharSequence[] uDatesFrom = new String[cryptoSymbols.size()];
            CharSequence[] uDatesTo = new String[cryptoSymbols.size()];
            for (int i = 0; i < cryptoSymbols.size(); ++i) {
                dataInfo = (DataInfo)cryptoSymbols.get(i);
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
            args.put("useCDN", new String[]{"true"});
            if (datesFrom != null && datesTo != null) {
                args.put("datesFrom", new String[]{String.join((CharSequence)",", uDatesFrom)});
                args.put("datesTo", new String[]{String.join((CharSequence)",", uDatesTo)});
            }
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DataSourceCryptoServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
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

