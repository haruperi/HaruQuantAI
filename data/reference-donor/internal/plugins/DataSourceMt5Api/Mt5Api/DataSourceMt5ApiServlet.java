/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.dukascopy.ImportInfo
 *  com.strategyquant.tradinglib.mt5api.Mt5ApiImportInfo
 *  com.strategyquant.tradinglib.mt5api.Mt5ApiManager
 *  com.strategyquant.tradinglib.mt5api.Mt5ApiManager$Source
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.joda.time.format.DateTimeFormat
 *  org.joda.time.format.DateTimeFormatter
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.Mt5Api;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.mt5api.Mt5ApiImportInfo;
import com.strategyquant.tradinglib.mt5api.Mt5ApiManager;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Comparator;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import org.joda.time.format.DateTimeFormat;
import org.joda.time.format.DateTimeFormatter;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataSourceMt5ApiServlet
extends HttpJSONServlet {
    private static final long serialVersionUID = 1L;
    DateTimeFormatter formaterDate = DateTimeFormat.forPattern((String)"yyyyMMdd");
    private static final Logger Log = LoggerFactory.getLogger(DataSourceMt5ApiServlet.class);

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "importData": {
                return this.onImportData(args);
            }
            case "downloadDataAction": {
                return this.onImportAction(args);
            }
            case "loadAvailableSymbols": {
                return this.onLoadAvailableSymbols(args);
            }
            case "updateSelected": {
                return this.updateSelected(args);
            }
        }
        return DataSourceMt5ApiServlet.apiErrorJSON((String)L.t((String)"Execution failed. Incorrect url arguments '%s'.", (Object[])new Object[]{command}), null);
    }

    private String updateSelected(Map<String, String[]> args) throws Exception {
        try {
            String[] symbols = this.tryGetParam(args, "symbols")[0].split(",");
            for (int i = 0; i < symbols.length; ++i) {
                String symbol = symbols[i];
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
                if (dataInfo == null) {
                    Log.error(String.format("Ticker '%s' not found. Failed to update data.", symbol));
                    continue;
                }
                Mt5ApiImportInfo importInfo = new Mt5ApiImportInfo();
                importInfo.origSymbol = dataInfo.uSymbol;
                importInfo.symbol = dataInfo.symbol;
                DownloadDispatcher.get().update(dataInfo, (ImportInfo)importInfo);
            }
        }
        catch (Exception e) {
            return DataSourceMt5ApiServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Update started.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onLoadAvailableSymbols(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        String source = "portable";
        String path = this.getParam(args, "path", null);
        List symbols = Mt5ApiManager.get().getSymbolListJson(Mt5ApiManager.Source.valueOf((String)source), path);
        if (symbols.isEmpty()) {
            DataSourceMt5ApiServlet.apiErrorJSON((String)"Error while fetching symbols list", null);
        }
        symbols.sort(new Comparator<JSONObject>(){

            @Override
            public int compare(JSONObject o1, JSONObject o2) {
                int compareCateg = o1.getString("path").compareTo(o2.getString("path"));
                if (compareCateg != 0) {
                    return compareCateg;
                }
                return o1.getString("name").compareTo(o2.getString("name"));
            }
        });
        response.put("symbols", (Object)symbols);
        response.put("success", (Object)L.t((String)"Symbols loaded.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onImportData(final Map<String, String[]> args) throws Exception {
        if (!args.containsKey("symbols")) {
            return DataSourceMt5ApiServlet.apiErrorJSON((String)L.t((String)"No symbols were specified", (Object[])new Object[0]), null);
        }
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onImportData(args);
        } else {
            new Thread(this){
                final /* synthetic */ DataSourceMt5ApiServlet this$0;
                {
                    this.this$0 = this$0;
                }

                @Override
                public void run() {
                    this.this$0._onImportData(args);
                }
            }.start();
        }
        JSONObject response = new JSONObject();
        response.put("success", (Object)L.t((String)"Data import started", (Object[])new Object[0]));
        return response.toString();
    }

    private void _onImportData(Map<String, String[]> args) {
        JSONObject progress = new JSONObject();
        try {
            String symbols = this.tryGetParam(args, "symbols")[0];
            String postfix = args.containsKey("postfix") ? this.tryGetParam(args, "postfix")[0] : "";
            String timeframe = "M1";
            int broker = Integer.valueOf(this.tryGetParamValue(args, "broker"));
            String[] symbolsArray = symbols.split(",");
            String source = "portable";
            String path = this.getParam(args, "path", null);
            LinkedList<Mt5ApiImportInfo> importInfoList = new LinkedList<Mt5ApiImportInfo>();
            for (int i = 0; i < symbolsArray.length; ++i) {
                String symbol = symbolsArray[i];
                String addedSymbol = this.addData(Mt5ApiManager.Source.valueOf((String)source), path, symbol, postfix, broker, timeframe);
                Integer percent = SQUtils.round((double)(100.0 * (double)i / (double)symbolsArray.length));
                progress.put("percent", (Object)percent);
                progress.put("info", (Object)L.t((String)"Adding symbol '%s'", (Object[])new Object[]{symbol}));
                DataManagerAddProgressSender.getInstance().sendData(progress);
                Mt5ApiImportInfo importInfo = new Mt5ApiImportInfo();
                importInfo.origSymbol = symbol;
                importInfo.symbol = addedSymbol;
                importInfo.path = path;
                importInfo.dateTo = args.containsKey("dateTo") ? SQTime.parseToMilis((String)this.tryGetParam(args, "dateTo")[0], (String)"yyyy.MM.dd") : System.currentTimeMillis();
                importInfo.dateFrom = args.containsKey("dateFrom") ? SQTime.parseToMilis((String)this.tryGetParam(args, "dateFrom")[0], (String)"yyyy.MM.dd") : SQTime.addYears((long)importInfo.dateTo, (int)-1);
                importInfoList.add(importInfo);
                progress.put("percent", (Object)percent);
                progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbol}));
                DataManagerAddProgressSender.getInstance().sendData(progress);
                SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)symbol, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            progress.put("percent", 100);
            progress.put("info", (Object)L.t((String)"Starting to download", (Object[])new Object[0]));
            DataManagerAddProgressSender.getInstance().sendData(progress);
            Log.info("Starting to download {} symbols", (Object)importInfoList.size());
            for (Mt5ApiImportInfo importInfo : importInfoList) {
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)importInfo.symbol);
                DownloadDispatcher.get().update(dataInfo, (ImportInfo)importInfo);
            }
        }
        catch (Exception e) {
            Log.error("Error while adding symbol", (Throwable)e);
            progress.put("percent", 100);
            progress.put("info", (Object)L.t((String)"Completed", (Object[])new Object[0]));
            progress.put("error", (Object)e.getMessage());
            DataManagerAddProgressSender.getInstance().sendData(progress);
        }
    }

    private String addData(Mt5ApiManager.Source source, String path, String symbol, String postfix, int broker, String timeframe) throws Exception {
        BrokerDto brokerDto = BrokerManager.getInstance().getBroker(Integer.valueOf(broker));
        if (brokerDto == null) {
            throw new RuntimeException("Specified broker was not found");
        }
        String symbolName = symbol + postfix;
        String instrumentName = symbol + postfix;
        while (DataManager.checkDataExists((String)"History", (String)symbolName)) {
            symbolName = DataManager.generateName((String)symbolName);
        }
        Map params = Mt5ApiManager.get().getSymbolInfoJson(source, path, symbol);
        double defaultSlippage = 0.0;
        byte instrumentType = 3;
        String desc = Mt5ApiManager.get().getDescription(params);
        if (desc.length() > 200) {
            desc = desc.substring(0, 200);
        }
        params = Mt5ApiManager.get().getPriceSymbolInfoJson(source, path, symbol);
        double tickSize = Mt5ApiManager.get().getTickSize(params);
        double tickStep = Mt5ApiManager.get().getTickStep(params);
        double pointValue = Mt5ApiManager.get().getPointValue(params);
        double defaultSpread = Mt5ApiManager.get().getDefaultSpread(params);
        if (!InstrumentManager.checkInstrumentExists((String)instrumentName)) {
            InstrumentManager.addInstrument((String)instrumentName, (String)("Mt5 Api instrument - " + desc), (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)instrumentType, null, null, null, null, (double)1.0, (double)0.0);
        } else {
            InstrumentInfo instrument = InstrumentManager.getInstrumentInfo((String)instrumentName);
            if (instrument.tickSize != tickSize || instrument.tickStep != tickStep) {
                while (InstrumentManager.checkInstrumentExists((String)instrumentName)) {
                    instrumentName = DataManager.generateName((String)instrumentName);
                }
                InstrumentManager.addInstrument((String)instrumentName, (int)broker, (String)"MT5 Api instrument", (double)pointValue, (double)tickSize, (double)tickStep, (double)defaultSpread, (double)defaultSlippage, (double)0.0, (String)"<Method type=\"None\" use=\"true\"><Params/></Method>", (byte)instrumentType, null, null, null, null, (double)1.0, (double)0.0);
            }
        }
        DataManager.addData((String)"History", (String)symbolName, (String)instrumentName, (int)1, (int)8, (String)symbol, (String)symbol, (int)-1, (int)broker);
        DataManager.updateTimeframe((String)"History", (String)symbolName, (String)timeframe);
        return symbolName;
    }

    private String onImportAction(Map<String, String[]> args) throws Exception {
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

