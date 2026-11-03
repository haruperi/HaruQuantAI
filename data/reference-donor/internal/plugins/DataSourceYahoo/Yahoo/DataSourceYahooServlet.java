/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Yahoo;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.plugin.DataSource.impl.Yahoo.YahooDataManager;
import com.strategyquant.plugin.DataSource.impl.Yahoo.YahooSymbol;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataSourceYahooServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DataSourceYahooServlet.class);
    private boolean canceled = false;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
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

    private String onAdd(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        String symbols = this.tryGetParam(args, "symbols")[0];
        ArrayList<String> symbolList = this.parseSymbols(symbols);
        final ArrayList<YahooSymbol> yahooSymbols = new ArrayList<YahooSymbol>();
        for (int i = 0; i < symbolList.size(); ++i) {
            String symbol = symbolList.get(i);
            YahooSymbol yahooSymbol = YahooDataManager.get().downloadInfo(symbol);
            yahooSymbols.add(yahooSymbol);
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onAdd(args, yahooSymbols);
        } else {
            new Thread(this){
                final /* synthetic */ DataSourceYahooServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    this.this$0._onAdd(args, yahooSymbols);
                }
            }.start();
        }
        response.put("success", (Object)L.t((String)"Add symbols.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _onAdd(Map<String, String[]> args, ArrayList<YahooSymbol> yahooSymbols) {
        JSONObject progress = new JSONObject();
        String error = null;
        try {
            String postfix = args.containsKey("postfix") ? this.tryGetParamValue(args, "postfix") : "";
            int percent = 0;
            for (int i = 0; i < yahooSymbols.size(); ++i) {
                YahooSymbol yahooSymbol = yahooSymbols.get(i);
                String symbolAdded = YahooDataManager.get().addData(yahooSymbol.symbol, postfix, (byte)1, yahooSymbol.name, yahooSymbol.exchange);
                DataManager.updateTimeframe((String)"History", (String)symbolAdded, (String)"D1");
                Log.info(String.format("Symbol '%s' added.", symbolAdded));
                percent = SQUtils.round((double)(100.0 * (double)i / (double)yahooSymbols.size()));
                progress.put("percent", percent);
                progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbolAdded}));
                DataManagerAddProgressSender.getInstance().sendData(progress);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)yahooSymbol.symbol, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
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

    private ArrayList<String> parseSymbols(String symbols) {
        String[] data = symbols.split("[\\n,;]+");
        ArrayList<String> list = new ArrayList<String>();
        for (String symbol : data) {
            if ((symbol = symbol.trim()).isEmpty()) continue;
            list.add(symbol);
        }
        return list;
    }

    private String onImportData(Map<String, String[]> args) throws Exception {
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
                    return DataSourceYahooServlet.apiErrorJSON((String)L.t((String)"Date from must be before Date to.", (Object[])new Object[0]), null);
                }
                DownloadDispatcher.get().update(dataInfo, importInfo);
            }
        }
        catch (Exception e) {
            return DataSourceYahooServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
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

    private String onUpdateAll() {
        try {
            ArrayList allSymbols = DataManager.list();
            ArrayList<DataInfo> yahooSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < allSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)allSymbols.get(i);
                if (dataInfo.source != 3 || dataInfo.sourceDataId != 0) continue;
                yahooSymbols.add((DataInfo)allSymbols.get(i));
            }
            if (yahooSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            CharSequence[] symbols = new String[yahooSymbols.size()];
            CharSequence[] uSymbols = new String[yahooSymbols.size()];
            for (int i = 0; i < yahooSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)yahooSymbols.get(i);
                symbols[i] = dataInfo.symbol;
                uSymbols[i] = dataInfo.uSymbol;
            }
            args.put("symbols", new String[]{String.join((CharSequence)",", symbols)});
            args.put("uSymbols", new String[]{String.join((CharSequence)",", uSymbols)});
            args.put("dateFrom", new String[]{"2013.01.01"});
            args.put("dateTo", new String[]{SQTime.toUIDateString((long)System.currentTimeMillis())});
            args.put("dateType", new String[]{"sinceLast"});
            args.put("overwrite", new String[]{"true"});
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DataSourceYahooServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
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
            ArrayList<DataInfo> yahooSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < symbols.length; ++i) {
                dataInfo = DataManager.getDataInfo((String)"History", (String)symbols[i]);
                if (dataInfo.source != 3 || dataInfo.sourceDataId != 0) continue;
                yahooSymbols.add(dataInfo);
            }
            if (yahooSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            symbols = new String[yahooSymbols.size()];
            CharSequence[] uSymbols = new String[yahooSymbols.size()];
            CharSequence[] uDatesFrom = new String[yahooSymbols.size()];
            CharSequence[] uDatesTo = new String[yahooSymbols.size()];
            for (int i = 0; i < yahooSymbols.size(); ++i) {
                dataInfo = (DataInfo)yahooSymbols.get(i);
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
            if (datesFrom != null && datesTo != null) {
                args.put("datesFrom", new String[]{String.join((CharSequence)",", uDatesFrom)});
                args.put("datesTo", new String[]{String.join((CharSequence)",", uDatesTo)});
            }
            return this.onImportData(args);
        }
        catch (Exception e) {
            return DataSourceYahooServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

