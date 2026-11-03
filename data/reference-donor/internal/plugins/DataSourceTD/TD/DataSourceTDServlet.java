/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.SymbolData
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DukasDataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.TD;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.SymbolData;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DukasDataManager;
import com.strategyquant.lib.L;
import com.strategyquant.plugin.DataSource.impl.TD.TDDataManager;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.File;
import java.util.Map;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataSourceTDServlet
extends HttpJSONServlet {
    DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyyMMdd");
    private static final Logger Log = LoggerFactory.getLogger(DataSourceTDServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "importData": {
                return this.onImportData(args);
            }
            case "importAction": {
                return this.onImportAction(args);
            }
            case "loadAvailableSymbols": {
                return this.onLoadAvailableSymbols(args);
            }
        }
        return DataSourceTDServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private String onLoadAvailableSymbols(Map<String, String[]> args) throws Exception {
        String path = this.tryGetParam(args, "path")[0];
        File f = new File(path + "//tickdata");
        if (f.exists()) {
            path = f.getAbsolutePath();
        }
        JSONObject response = new JSONObject();
        JSONArray symbols = new JSONArray();
        try {
            File folder = new File(path);
            File[] files = folder.listFiles();
            if (files != null) {
                for (int i = 0; i < files.length; ++i) {
                    f = files[i];
                    if (!f.isDirectory()) continue;
                    symbols.put((Object)f.getName());
                }
            }
        }
        catch (Exception e) {
            return DataSourceTDServlet.apiErrorJSON((String)L.t((String)"Cannot load available symbols.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("symbols", (Object)symbols);
        response.put("success", (Object)L.t((String)"Symbols loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportData(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        try {
            String symbol;
            int i;
            String symbols = this.tryGetParam(args, "symbols")[0];
            String postfix = args.containsKey("postfix") ? this.tryGetParam(args, "postfix")[0] : "";
            String path = this.tryGetParam(args, "path")[0];
            File f = new File(path + "//tickdata");
            if (f.exists()) {
                path = f.getAbsolutePath();
            }
            String[] symbolsArray = symbols.split(",");
            for (i = 0; i < symbolsArray.length; ++i) {
                symbol = symbolsArray[i];
                DataInfo info = DataManager.getDataInfo((String)"History", (String)(symbol + postfix));
                if (info == null) continue;
                throw new Exception(L.t((String)"Symbol with name '%s' already exists. Please enter a postfix to generate unique symbol names.", (Object[])new Object[]{symbol}));
            }
            for (i = 0; i < symbolsArray.length; ++i) {
                symbol = symbolsArray[i];
                DukasDataManager.get().addData(symbol, postfix, -1, null);
                ImportInfo importInfo = new ImportInfo();
                importInfo.origSymbol = symbol;
                importInfo.symbol = symbol + postfix;
                importInfo.overwrite = true;
                DataInfo info = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
                importInfo.instrumentInfo = info.symbolInfo;
                importInfo.rows = info.rows;
                importInfo.oldDateFrom = info.dateFrom;
                importInfo.oldDateTo = info.dateTo;
                SymbolData symbolData = DukasDataManager.get().getAvailableDataInfo(importInfo.origSymbol);
                importInfo.priceConstant = Math.pow(10.0, -symbolData.decimals);
                DataManagerProgressListener listener = (DataManagerProgressListener)DataManagerDataProgress.get().createListener(symbol + postfix, "dataSourceTD/importAction");
                TDDataManager.get().importTDData(importInfo, path, listener);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbols, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            return DataSourceTDServlet.apiErrorJSON((String)L.t((String)"Cannot import data.", (Object[])new Object[0]), (Throwable)e);
        }
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportAction(Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbol", "action"});
        String symbol = this.tryGetParam(args, "symbol")[0];
        String action = this.tryGetParam(args, "action")[0];
        JSONObject response = new JSONObject();
        switch (action) {
            case "stop": {
                TDDataManager.get().stopTDImport(symbol);
                break;
            }
            case "pause": {
                TDDataManager.get().pauseTDImport(symbol);
                break;
            }
            case "continue": {
                TDDataManager.get().restartTDImport(symbol);
            }
        }
        response.put("success", (Object)"ok");
        return response.toString();
    }
}

