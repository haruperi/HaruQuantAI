/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.BatchProgressController
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DownloadSemaphore
 *  com.strategyquant.datalib.data.DukasDataManager
 *  com.strategyquant.datalib.data.InstrumentValueEvaluator
 *  com.strategyquant.datalib.data.StockGroupUpdateErrorManager
 *  com.strategyquant.datalib.historyData.TickerFilterDto
 *  com.strategyquant.datalib.historyData.dto.TickerDto
 *  com.strategyquant.datalib.historyData.dto.TickerKind
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.historyData.HistoryDataSubscription
 *  com.strategyquant.model.IdName
 *  com.strategyquant.tradinglib.data.download.DownloadDispatcher
 *  com.strategyquant.tradinglib.historyData.HistoryDataManager
 *  com.strategyquant.tradinglib.historyData.MarketDtoToJsonTransformer
 *  com.strategyquant.tradinglib.historyData.TickerDtoToJsonTransformer
 *  com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.MultiProgressListener
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.project.websocket.WebSocketNotification
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.SQEquityData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.BatchProgressController;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DownloadSemaphore;
import com.strategyquant.datalib.data.DukasDataManager;
import com.strategyquant.datalib.data.InstrumentValueEvaluator;
import com.strategyquant.datalib.data.StockGroupUpdateErrorManager;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.TickerDto;
import com.strategyquant.datalib.historyData.dto.TickerKind;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.historyData.HistoryDataSubscription;
import com.strategyquant.model.IdName;
import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.historyData.MarketDtoToJsonTransformer;
import com.strategyquant.tradinglib.historyData.TickerDtoToJsonTransformer;
import com.strategyquant.tradinglib.project.websocket.DataManagerAddProgressSender;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQEquityDataServlet
extends HttpJSONServlet {
    private static final String JOB_PREFIX = "HistoryDownloadJob_";
    private static final Logger Log = LoggerFactory.getLogger(SQEquityDataServlet.class);
    private boolean canceled = false;
    private String exchangesResponse = null;

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "getExchanges": {
                return this.onGetExchanges();
            }
            case "add": {
                return this.onAdd(args);
            }
            case "addCancel": {
                return this.onAddCancel();
            }
            case "lookup": {
                return this.onLookup(args);
            }
            case "update": {
                return this.onUpdate();
            }
            case "verifySubscription": {
                return this.onVerifySubscription(args);
            }
            case "updateDataAction": {
                return this.onUpdateDataAction(args);
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

    private String onGetExchanges() throws Exception {
        if (this.exchangesResponse != null) {
            return this.exchangesResponse;
        }
        JSONObject response = new JSONObject();
        List markets = HistoryDataManager.get().getStockMarkets();
        markets.add(0, new IdName(Long.valueOf(0L), L.t((String)"Any", (Object[])new Object[0])));
        JSONArray exchanges = new MarketDtoToJsonTransformer().toJson(markets);
        response.put("exchanges", (Object)exchanges);
        response.put("success", (Object)L.t((String)"Exchanges listed.", (Object[])new Object[0]));
        this.exchangesResponse = response.toString();
        return this.exchangesResponse;
    }

    private String onAdd(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols", "barType"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onAdd(args);
        } else {
            new Thread(this){
                final /* synthetic */ SQEquityDataServlet this$0;
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
        final JSONObject progress = new JSONObject();
        String error = null;
        try {
            String rawSymbols = this.tryGetParamValue(args, "symbols");
            final String[] symbols = rawSymbols.equals("") ? new String[]{} : rawSymbols.split(",");
            String postfix = args.containsKey("postfix") ? this.tryGetParamValue(args, "postfix") : "";
            int barType = Integer.parseInt(this.tryGetParam(args, "barType")[0]);
            if (barType != 1 && barType != 2) {
                throw new IllegalArgumentException("Unknown bar time type: " + barType);
            }
            int timezoneType = Integer.parseInt(this.getParam(args, "timezoneType", "2"));
            int timezoneShift = Integer.parseInt(this.getParam(args, "timezoneShift", "0"));
            String timezone = this.getParam(args, "timezone", "EETUS");
            String updateSymbols = this.getParam(args, "updateSymbols", null);
            String strTimeZone = null;
            strTimeZone = timezoneType == 2 ? "Exchange" : (timezoneType == 1 ? timezone : "Exchange " + (timezoneShift < 0 ? Integer.valueOf(timezoneShift) : "+" + timezoneShift));
            TickerFilterDto filter = new TickerFilterDto();
            filter.setSearchInTicker(true);
            filter.setExactMatch(true);
            filter.setNames(symbols);
            List tickers = HistoryDataManager.get().getStockTickers(filter);
            LinkedList<String> eodSymbols = new LinkedList<String>();
            LinkedList<String> m1Symbols = new LinkedList<String>();
            for (TickerDto tickerDto : tickers) {
                if (tickerDto.isEod()) {
                    eodSymbols.add(tickerDto.getTicker());
                    continue;
                }
                m1Symbols.add(tickerDto.getTicker());
            }
            this.subscriptionCheck(eodSymbols.toArray(new String[0]), true);
            this.subscriptionCheck(m1Symbols.toArray(new String[0]), false);
            Map<String, TickerDto> tickerMap = tickers.stream().collect(Collectors.toMap(TickerDto::getTicker, i -> i));
            ArrayList<DataInfo> dataInfos = new ArrayList<DataInfo>(symbols.length);
            for (int i2 = 0; i2 < symbols.length; ++i2) {
                String instrumentName;
                String symbol = symbols[i2];
                TickerDto ticker = tickerMap.get(symbol);
                if (ticker == null) {
                    Log.error(String.format("Ticker '%s' not found. Failed to add data.", symbol));
                    StockGroupUpdateErrorManager.getInstance().logError(symbol, "Ticker '" + symbol + "' not found. Failed to add data.");
                    continue;
                }
                DataInfo info = new DataInfo();
                dataInfos.add(info);
                info.barTimeType = barType;
                info.timezone = strTimeZone;
                info.connection = "History";
                info.symbol = symbol + postfix;
                info.source = 5;
                info.instrument = instrumentName = ticker.getMarketName().replaceAll("Common ", "").trim() + " " + ticker.getType();
                info.uSymbol = ticker.getTicker();
            }
            int total = symbols.length;
            int batchSize = total / 20;
            if (batchSize < 10) {
                batchSize = 10;
            }
            final HashSet symbolsSet = new HashSet();
            final int batchSizeForUse = batchSize;
            DukasDataManager.get().addBatch(dataInfos, tickerMap, new InstrumentValueEvaluator(){

                public double getTickStep(TickerDto ticker) {
                    return 1.0E-4;
                }

                public double getTickSize(TickerDto ticker) {
                    return 0.01;
                }

                public double getPointValue(TickerDto ticker) {
                    return 1.0;
                }

                public byte getInstrumentType(TickerDto ticker) {
                    return ticker.getType().contains("ETF") ? (byte)5 : 1;
                }

                public String getDescriptions(TickerDto ticker) {
                    return "History data instrument";
                }

                public double getOrderSizeMultiplier(TickerDto ticker) {
                    return 1.0;
                }

                public double getOrderSizeStep(TickerDto ticker) {
                    return 0.0;
                }
            }, new BatchProgressController(){
                final /* synthetic */ SQEquityDataServlet this$0;
                {
                    this.this$0 = this$0;
                }

                public void updateProgress(int count, int total, String symbol) throws Exception {
                    if (count % batchSizeForUse == 0) {
                        Integer percent = SQUtils.round((double)(100.0 * (double)count / (double)total));
                        progress.put("percent", (Object)percent);
                        progress.put("info", (Object)L.t((String)"Added symbol '%s'", (Object[])new Object[]{symbol}));
                        DataManagerAddProgressSender.getInstance().sendData(progress);
                        symbolsSet.clear();
                        StringBuilder sb = new StringBuilder();
                        for (int i = count - batchSizeForUse; i <= count && i < symbols.length; ++i) {
                            symbolsSet.add(symbols[i]);
                            if (sb.length() != 0) {
                                sb.append(",");
                            }
                            sb.append(symbols[i]);
                        }
                        SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((Set)symbolsSet, (String)sb.toString(), (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
                    }
                }

                public boolean isCancel() {
                    return this.this$0.canceled;
                }

                public void finished() {
                }
            });
            if (updateSymbols != null) {
                WebSocketNotification.sendSuccess((String)L.t((String)"Symbols %s added to databank. Starting to download data.", (Object[])new Object[]{dataInfos.size()}), (String[])new String[]{"QDM", "SQUANT"});
                HashMap<String, String[]> args2 = new HashMap<String, String[]>();
                args2.put("symbols", new String[]{updateSymbols});
                this.onUpdateSelected(args2);
            }
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)rawSymbols, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
        }
        catch (Exception e) {
            Log.error("Cannot add symbols. Exc.", (Throwable)e);
            error = e.getMessage();
        }
        finally {
            DownloadSemaphore.getInstance().downloadFinished();
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

    private void subscriptionCheck(String[] symbols, boolean eod) throws Exception {
        for (String symbol : symbols) {
            if (eod) {
                if (HistoryDataSubscription.getInstance().isAllowedEquity(symbol, true)) continue;
                throw new Exception(L.t((String)"Cannot add ticker '%s'. EOD data subscription not active.", (Object[])new Object[]{symbol}));
            }
            if (HistoryDataSubscription.getInstance().isAllowedEquity(symbol, false)) continue;
            throw new Exception(L.t((String)"Cannot add ticker '%s'. Intraday data subscription not active.", (Object[])new Object[]{symbol}));
        }
    }

    private String onLookup(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        boolean searchInName = Boolean.parseBoolean(args.get("searchInName")[0]);
        boolean searchInTicker = Boolean.parseBoolean(args.get("searchInTicker")[0]);
        boolean exactMatch = Boolean.parseBoolean(args.get("exact")[0]);
        if (!searchInName && !searchInTicker) {
            throw new Exception(L.t((String)"Search method not set.", (Object[])new Object[0]));
        }
        TickerFilterDto filter = new TickerFilterDto();
        filter.setExactMatch(searchInTicker && exactMatch);
        filter.setSearchInName(searchInName);
        filter.setSearchInTicker(searchInTicker);
        if (args.containsKey("symbols")) {
            filter.setNames(this.tryGetParamValue(args, "symbols").split("[\\n,;]+"));
        }
        try {
            String exchange = this.tryGetParamValue(args, "exchange");
            filter.setMarketId(Long.valueOf(exchange));
        }
        catch (Exception exchange) {
            // empty catch block
        }
        if (filter.getMarketId() == 0L && filter.getNames() == null) {
            throw new Exception(L.t((String)"Exchange or text must be set", (Object[])new Object[0]));
        }
        List tickers = HistoryDataManager.get().getStockTickers(filter);
        response.put("tickers", (Object)new TickerDtoToJsonTransformer(TickerKind.STOCK).toJson(tickers));
        response.put("success", (Object)L.t((String)"Data lookup.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdate() throws Exception {
        ArrayList stockSymbols = DataManager.listForSource((int)5);
        return this.performUpdate(stockSymbols);
    }

    private String performUpdate(ArrayList<DataInfo> stockSymbols) throws Exception {
        JSONObject response = new JSONObject();
        if (stockSymbols.isEmpty()) {
            response.put("success", (Object)L.t((String)"No symbols to update.", (Object[])new Object[0]));
            return response.toString();
        }
        List<String> symbolList = stockSymbols.stream().filter(i -> i.uSymbol != null).map(i -> i.uSymbol).collect(Collectors.toList());
        TickerFilterDto filter = new TickerFilterDto();
        filter.setSearchInTicker(true);
        filter.setExactMatch(true);
        filter.setNames(symbolList.toArray(new String[0]));
        List recordsFromDb = HistoryDataManager.get().getStockTickers(filter);
        Map<String, TickerDto> recordsMap = recordsFromDb.stream().collect(Collectors.toMap(TickerDto::getTicker, i -> i));
        LinkedList<DataInfo> filteredInfos = new LinkedList<DataInfo>();
        for (DataInfo dataInfo : stockSymbols) {
            if (dataInfo.uSymbol == null || !this.isDownloadAllowed(dataInfo) || DataManager.isLimited((String)dataInfo.symbol)) continue;
            filteredInfos.add(dataInfo);
        }
        DownloadDispatcher.get().updateHistoryData(filteredInfos, recordsMap);
        if (!stockSymbols.isEmpty() && filteredInfos.isEmpty()) {
            throw new RuntimeException(L.t((String)"You don't have subscriptions for requested data.", (Object[])new Object[0]));
        }
        response.put("success", (Object)L.t((String)"Update started.", (Object[])new Object[0]));
        return response.toString();
    }

    private boolean isDownloadAllowed(DataInfo dataInfo) {
        String timeframe = dataInfo.timeframe;
        boolean eod = !timeframe.equals("M1");
        return HistoryDataSubscription.getInstance().isAllowedEquity(dataInfo.uSymbol, eod);
    }

    private String onVerifySubscription(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        HistoryDataSubscription subscription = HistoryDataSubscription.getInstance();
        response.put("eodSubscriptionActive", subscription.isEquitiesEODActive());
        response.put("minuteSubscriptionActive", subscription.isEquitiesMinuteActive());
        response.put("freeEquities", (Object)subscription.getFreeEquities());
        response.put("success", (Object)L.t((String)"Subscription verified.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdateDataAction(Map<String, String[]> args) throws Exception {
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

    private String onUpdateAll() throws Exception {
        return this.onUpdate();
    }

    private String onUpdateSelected(Map<String, String[]> map) throws Exception {
        try {
            String[] symbols = this.tryGetParam(map, "symbols")[0].split(",");
            ArrayList<DataInfo> stockSymbols = new ArrayList<DataInfo>();
            for (int i = 0; i < symbols.length; ++i) {
                String symbol = symbols[i];
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbol);
                if (dataInfo == null) {
                    Log.error(String.format("Ticker '%s' not found. Failed to update data.", symbol));
                    continue;
                }
                if (dataInfo.source != 5 || dataInfo.sourceDataId != 0) continue;
                stockSymbols.add(dataInfo);
            }
            return this.performUpdate(stockSymbols);
        }
        catch (Exception e) {
            return SQEquityDataServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

