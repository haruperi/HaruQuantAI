/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.SymbolData
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.DataSources
 *  com.strategyquant.qdm.QDM
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener
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
package com.strategyquant.plugin.DataSource.impl.Darwinex;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.SymbolData;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.DataSources;
import com.strategyquant.plugin.DataSource.impl.Darwinex.DarwinexDataManager;
import com.strategyquant.plugin.DataSource.impl.Darwinex.importdata.DarwinexImport;
import com.strategyquant.qdm.QDM;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(DarwinexServlet.class);
    private boolean canceled = false;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "importData": {
                return this.onImportData(args);
            }
            case "importDataCancel": {
                return this.onImportDataCancel();
            }
            case "addData": {
                return this.onAddData(args);
            }
            case "importAction": {
                return this.onImportAction(args);
            }
            case "importLoadAvailableSymbols": {
                return this.onImportLoadAvailableSymbols(args);
            }
            case "downloadGetDataList": {
                return this.onDownloadGetDataList();
            }
            case "downloadAddData": {
                return this.onDownloadAddData(args);
            }
            case "downloadData": {
                return this.onDownloadData(args);
            }
            case "downloadDataAction": {
                return this.onDownloadDataAction(args);
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

    private String onAddCancel() throws Exception {
        JSONObject response = new JSONObject();
        this.canceled = true;
        response.put("success", (Object)L.t((String)"Adding symbols canceled.", (Object[])new Object[0]));
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
                final /* synthetic */ DarwinexServlet this$0;
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
            String timeframe = "TICK";
            int broker = Integer.valueOf(this.tryGetParamValue(args, "broker"));
            int percent = 0;
            for (int i = 0; i < symbols.length; ++i) {
                String instrument;
                String symbol = symbols[i];
                String string = instrument = instruments == null ? null : instruments[i];
                if (instrument != null && instrument.equals("-1")) {
                    instrument = null;
                }
                String symbolAdded = DarwinexDataManager.get().addData(symbol, postfix, broker, instrument);
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

    private String onImportLoadAvailableSymbols(Map<String, String[]> args) throws Exception {
        JSONArray symbols;
        JSONObject response;
        block5: {
            String path = this.tryGetParam(args, "path")[0];
            response = new JSONObject();
            symbols = new JSONArray();
            try {
                File f;
                File folder = new File(path);
                File[] files = folder.listFiles();
                if (files == null) break block5;
                block2: for (int i = 0; i < files.length; ++i) {
                    File[] tickFiles;
                    f = files[i];
                    if (!f.isDirectory() || (tickFiles = f.listFiles()) == null) continue;
                    for (int t = 0; t < tickFiles.length; ++t) {
                        if (!tickFiles[t].getName().endsWith("log.gz")) continue;
                        symbols.put((Object)f.getName());
                        continue block2;
                    }
                }
                if (symbols.length() != 0) break block5;
                String symbol = folder.getName();
                if (DarwinexDataManager.get().getAvailableDataInfo(symbol) == null) break block5;
                for (int i = 0; i < files.length; ++i) {
                    f = files[i];
                    if (f.isDirectory() || !f.getName().endsWith("log.gz")) continue;
                    symbols.put((Object)symbol);
                    break;
                }
            }
            catch (Exception e) {
                return DarwinexServlet.apiErrorJSON((String)L.t((String)"Cannot load available symbols.", (Object[])new Object[0]), (Throwable)e);
            }
        }
        response.put("symbols", (Object)symbols);
        response.put("success", (Object)L.t((String)"Symbols loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportData(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols", "path"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onImportData(args);
        } else {
            new Thread(this){
                final /* synthetic */ DarwinexServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    this.this$0._onImportData(args);
                }
            }.start();
        }
        response.put("success", (Object)L.t((String)"Add darwinex data.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportDataCancel() throws Exception {
        JSONObject response = new JSONObject();
        this.canceled = true;
        response.put("success", (Object)L.t((String)"Adding symbols canceled.", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private void _onImportData(Map<String, String[]> args) {
        JSONObject progress = new JSONObject();
        String error = null;
        try {
            File folder;
            String rawSymbols = this.tryGetParam(args, "symbols")[0];
            String postfix = args.containsKey("postfix") ? this.tryGetParam(args, "postfix")[0] : "";
            String path = this.tryGetParam(args, "path")[0];
            String[] symbols = rawSymbols.split(",");
            if (symbols.length == 1 && !(folder = new File(new File(path), symbols[0])).exists()) {
                path = new File(path).getParentFile().getAbsolutePath();
            }
            int percent = 0;
            for (int i = 0; i < symbols.length; ++i) {
                String symbol = symbols[i];
                try {
                    String symbolAdded = DarwinexDataManager.get().addData(symbol, postfix, -1, null);
                    Log.info(String.format("Symbol '%s' added.", symbolAdded));
                    ImportInfo importInfo = new ImportInfo();
                    importInfo.origSymbol = symbol;
                    importInfo.symbol = symbolAdded;
                    importInfo.overwrite = true;
                    DataInfo info = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
                    importInfo.instrumentInfo = info.symbolInfo;
                    importInfo.rows = info.rows;
                    importInfo.oldDateFrom = info.dateFrom;
                    importInfo.oldDateTo = info.dateTo;
                    importInfo.priceConstant = Math.pow(10.0, -info.decimals);
                    DataManagerProgressListener listener = (DataManagerProgressListener)DataManagerDataProgress.get().createListener(symbolAdded, "darwinex/importAction");
                    DarwinexImport.get().importData(importInfo, path, listener);
                    percent = SQUtils.round((double)(100.0 * (double)i / (double)symbols.length));
                    progress.put("percent", percent);
                    progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbolAdded}));
                    DataManagerAddProgressSender.getInstance().sendData(progress);
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)rawSymbols, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    if (!this.canceled) continue;
                    break;
                }
                catch (Exception ex) {
                    error = L.t((String)"Some symbols cannot be added.", (Object[])new Object[0]) + " " + ex.getMessage();
                    Log.error(L.t((String)"Cannot add symbol %s. Reason: %s", (Object[])new Object[]{symbol, ex.getMessage()}), (Throwable)ex);
                }
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

    private String onImportAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        switch (action) {
            case "stop": {
                DarwinexImport.get().stop(symbol);
                break;
            }
            case "pause": {
                DarwinexImport.get().pause(symbol);
                break;
            }
            case "continue": {
                DarwinexImport.get().restart(symbol);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private String onDownloadGetDataList() {
        JSONObject response = new JSONObject();
        JSONArray dataArray = new JSONArray();
        for (SymbolData data : DarwinexDataManager.get().getAvailableDataList()) {
            JSONObject dataObj = new JSONObject();
            dataObj.put("symbol", (Object)data.symbol);
            dataObj.put("dateFrom", data.dateFrom);
            dataObj.put("decimals", data.decimals);
            dataObj.put("tickValue", data.tickValue);
            dataObj.put("defaultSpread", data.defaultSpread);
            dataObj.put("tickSize", data.tickSize);
            dataObj.put("tickStep", data.tickStep);
            dataObj.put("instrumentType", (int)data.instrumentType);
            dataArray.put((Object)dataObj);
        }
        response.put("data", (Object)dataArray);
        response.put("success", (Object)L.t((String)"Data listed", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDownloadAddData(final Map<String, String[]> args) {
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            return this._onDownloadAddData(args);
        }
        new Thread(this){
            final /* synthetic */ DarwinexServlet this$0;
            {
                this.this$0 = this$0;
            }

            @Override
            public void run() {
                this.this$0._onDownloadAddData(args);
            }
        }.start();
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Data added", (Object[])new Object[0]));
        return response.toString();
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String _onDownloadAddData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        double percent = 0.0;
        try {
            String postfix = args.containsKey("postfix") ? this.tryGetParam(args, "postfix")[0] : "";
            String[] symbols = this.tryGetParam(args, "symbols[]");
            int broker = Integer.valueOf(this.tryGetParamValue(args, "broker"));
            String[] instruments = args.containsKey("instruments[]") ? this.tryGetParam(args, "instruments[]") : null;
            for (int i = 0; i < symbols.length; ++i) {
                String instrument;
                String symbol = symbols[i];
                String string = instrument = instruments == null ? null : instruments[i];
                if (instrument != null && instrument.equals("-1")) {
                    instrument = null;
                }
                String symbolAdded = DarwinexDataManager.get().addData(symbol, postfix, broker, instrument);
                DataManager.updateTimeframe((String)"History", (String)symbolAdded, (String)"TICK");
                percent = SQUtils.round((double)(100.0 * (double)i / (double)symbols.length)).intValue();
                response.put("percent", percent);
                response.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbol}));
                DataManagerAddProgressSender.getInstance().sendData(response);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbol, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                if (!this.canceled) continue;
                break;
            }
        }
        catch (Exception e) {
            String string = DarwinexServlet.apiErrorJSON((String)L.t((String)"Cannot add data.", (Object[])new Object[0]), (Throwable)e);
            return string;
        }
        finally {
            response.put("percent", 100);
            response.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
            DataManagerAddProgressSender.getInstance().sendData(response);
        }
        response.put("success", (Object)L.t((String)"Data added", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDownloadData(Map<String, String[]> args) {
        JSONObject response = new JSONObject();
        try {
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
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
            HashMap jobs = new HashMap();
            HashMap listeners = new HashMap();
            for (int a = 0; a < symbols.length; ++a) {
                String symbol = symbols[a];
                DataInfo info = DataManager.getDataInfo((String)"History", (String)symbol);
                if (info.source != 4) continue;
                if (datesFrom != null && datesTo != null) {
                    dateFrom = SQTime.parseToMilis((String)datesFrom[a], (String)"yyyy.MM.dd");
                    dateTo = SQTime.parseToMilis((String)datesTo[a], (String)"yyyy.MM.dd");
                }
                ImportInfo importInfo = new ImportInfo();
                importInfo.symbol = symbol;
                importInfo.overwrite = overwrite;
                importInfo.origSymbol = info.uSymbol;
                importInfo.instrumentInfo = info.symbolInfo;
                importInfo.rows = info.rows;
                importInfo.oldDateFrom = info.dateFrom;
                importInfo.oldDateTo = info.dateTo;
                importInfo.ignoreWeekend = info.symbolInfo.dataType == 3;
                SymbolData symbolData = DarwinexDataManager.get().getAvailableDataInfo(importInfo.origSymbol);
                if (symbolData == null) {
                    throw new Exception(L.t((String)"No info found for symbol '%s'.", (Object[])new Object[]{importInfo.origSymbol}));
                }
                importInfo.priceConstant = Math.pow(10.0, -symbolData.decimals);
                importInfo.downloadM1Data = false;
                importInfo.dateFrom = dateFrom;
                importInfo.dateTo = dateTo;
                importInfo.downloadType = downloadType;
                importInfo.useCDN = true;
                if (dateType.equals("allTime")) {
                    importInfo.dateFrom = symbolData.dateFrom;
                } else if (dateType.equals("sinceLast")) {
                    long l = importInfo.dateFrom = info.dateTo > 0L ? info.dateTo : symbolData.dateFrom;
                }
                if (importInfo.dateFrom > importInfo.dateTo) {
                    return DarwinexServlet.apiErrorJSON((String)L.t((String)"Date from must be before Date to.", (Object[])new Object[0]), null);
                }
                QDM.getInstance().activity.increase(3);
                DownloadDispatcher.get().update(info, importInfo);
            }
        }
        catch (Exception e) {
            return DarwinexServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
    }

    private String onDownloadDataAction(Map<String, String[]> args) throws Exception {
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
            ArrayList<DataInfo> darwinexSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < allSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)allSymbols.get(i);
                if (dataInfo.source != 4 || dataInfo.sourceDataId != 0) continue;
                darwinexSymbols.add((DataInfo)allSymbols.get(i));
            }
            if (darwinexSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            CharSequence[] symbols = new String[darwinexSymbols.size()];
            CharSequence[] uSymbols = new String[darwinexSymbols.size()];
            for (int i = 0; i < darwinexSymbols.size(); ++i) {
                DataInfo dataInfo = (DataInfo)darwinexSymbols.get(i);
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
            return this.onDownloadData(args);
        }
        catch (Exception e) {
            return DarwinexServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
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
            ArrayList<DataInfo> darwinexSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < symbols.length; ++i) {
                dataInfo = DataManager.getDataInfo((String)"History", (String)symbols[i]);
                if (dataInfo.source != 4 || dataInfo.sourceDataId != 0) continue;
                dataInfo.dateFromStr = datesFrom == null ? null : datesFrom[i];
                dataInfo.dateToStr = datesTo == null ? null : datesTo[i];
                darwinexSymbols.add(dataInfo);
            }
            if (darwinexSymbols.isEmpty()) {
                return "No symbols to update";
            }
            HashMap<String, String[]> args = new HashMap<String, String[]>();
            symbols = new String[darwinexSymbols.size()];
            CharSequence[] uSymbols = new String[darwinexSymbols.size()];
            CharSequence[] uDatesFrom = new String[darwinexSymbols.size()];
            CharSequence[] uDatesTo = new String[darwinexSymbols.size()];
            for (int i = 0; i < darwinexSymbols.size(); ++i) {
                dataInfo = (DataInfo)darwinexSymbols.get(i);
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
            if (datesFrom != null && datesTo != null) {
                args.put("datesFrom", new String[]{String.join((CharSequence)",", uDatesFrom)});
                args.put("datesTo", new String[]{String.join((CharSequence)",", uDatesTo)});
            }
            return this.onDownloadData(args);
        }
        catch (Exception e) {
            return DarwinexServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

