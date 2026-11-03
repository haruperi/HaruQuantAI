/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.BatchProgressController
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.DukasDataManager
 *  com.strategyquant.datalib.data.InstrumentValueEvaluator
 *  com.strategyquant.datalib.historyData.TickerFilterDto
 *  com.strategyquant.datalib.historyData.dto.CommodityDto
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
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.apache.http.client.ClientProtocolException
 *  org.jdom2.JDOMException
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataSource.impl.SQFuturesData;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.BatchProgressController;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.DukasDataManager;
import com.strategyquant.datalib.data.InstrumentValueEvaluator;
import com.strategyquant.datalib.historyData.TickerFilterDto;
import com.strategyquant.datalib.historyData.dto.CommodityDto;
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
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.io.IOException;
import java.security.NoSuchAlgorithmException;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.apache.http.client.ClientProtocolException;
import org.jdom2.JDOMException;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SQFuturesDataServlet
extends HttpJSONServlet {
    private static final String JOB_PREFIX = "HistoryDownloadJob_";
    private static final Logger Log = LoggerFactory.getLogger(SQFuturesDataServlet.class);
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
            case "updateBr": {
                return this.onUpdateBr();
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
        List markets = HistoryDataManager.get().getFuturesMarkets();
        markets.add(0, new IdName(Long.valueOf(0L), L.t((String)"Any", (Object[])new Object[0])));
        JSONArray exchanges = new MarketDtoToJsonTransformer().toJson(markets);
        response.put("exchanges", (Object)exchanges);
        response.put("success", (Object)L.t((String)"Exchanges listed.", (Object[])new Object[0]));
        this.exchangesResponse = response.toString();
        return this.exchangesResponse;
    }

    private String onAdd(final Map<String, String[]> args) throws Exception {
        this.checkParamExists(args, new String[]{"symbols", "barType", "timezoneType"});
        JSONObject response = new JSONObject();
        this.canceled = false;
        if (MainApp.runInConsoleWithoutActiveWebserver()) {
            this._onAdd(args);
        } else {
            new Thread(this){
                final /* synthetic */ SQFuturesDataServlet this$0;
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
            final String[] symbols = rawSymbols.split(",");
            String postfix = args.containsKey("postfix") ? this.tryGetParamValue(args, "postfix") : "";
            int barType = Integer.parseInt(this.tryGetParam(args, "barType")[0]);
            if (barType != 1 && barType != 2) {
                throw new IllegalArgumentException("Unknown bar time type: " + barType);
            }
            int timezoneType = Integer.parseInt(this.tryGetParam(args, "timezoneType")[0]);
            int timezoneShift = Integer.parseInt(this.tryGetParam(args, "timezoneShift")[0]);
            String timezone = this.tryGetParamValue(args, "timezone");
            String strTimeZone = null;
            strTimeZone = timezoneType == 2 ? "Exchange" : (timezoneType == 1 ? timezone : "Exchange " + (timezoneShift < 0 ? Integer.valueOf(timezoneShift) : "+" + timezoneShift));
            List commodities = HistoryDataManager.get().getCommodities(symbols);
            final Map<Long, CommodityDto> commodityMap = commodities.stream().collect(Collectors.toMap(CommodityDto::getId, i -> i));
            TickerFilterDto filter = new TickerFilterDto();
            filter.setSearchInTicker(true);
            filter.setExactMatch(true);
            filter.setNames(symbols);
            List tickers = HistoryDataManager.get().getFuturesTickers(filter);
            LinkedList<String> eodSymbols = new LinkedList<String>();
            LinkedList<String> m1Symbols = new LinkedList<String>();
            for (TickerDto tickerDto : tickers) {
                if (tickerDto.isEod()) {
                    eodSymbols.add(tickerDto.getTicker());
                    continue;
                }
                m1Symbols.add(tickerDto.getTicker());
            }
            Map<String, TickerDto> tickerMap = tickers.stream().collect(Collectors.toMap(TickerDto::getTicker, i -> i));
            this.subscriptionCheck(eodSymbols.toArray(new String[0]), tickerMap, true);
            this.subscriptionCheck(m1Symbols.toArray(new String[0]), tickerMap, false);
            ArrayList<DataInfo> dataInfos = new ArrayList<DataInfo>(symbols.length);
            for (int i2 = 0; i2 < symbols.length; ++i2) {
                String symbol = symbols[i2];
                TickerDto ticker = tickerMap.get(symbol);
                DataInfo info = new DataInfo();
                dataInfos.add(info);
                info.barTimeType = barType;
                info.timezone = strTimeZone;
                info.connection = "History";
                info.symbol = symbol + postfix;
                info.source = 6;
                CommodityDto commodity = commodityMap.get(ticker.getCommodityId());
                info.instrument = commodity.getCode() + " - " + ticker.getMarketName().replaceAll("Common ", "");
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
                final /* synthetic */ SQFuturesDataServlet this$0;
                {
                    this.this$0 = this$0;
                }

                public double getTickStep(TickerDto ticker) {
                    CommodityDto commodity = (CommodityDto)commodityMap.get(ticker.getCommodityId());
                    return commodity.getTickStep().doubleValue();
                }

                public double getTickSize(TickerDto ticker) {
                    CommodityDto commodity = (CommodityDto)commodityMap.get(ticker.getCommodityId());
                    return commodity.getTickSize().doubleValue();
                }

                public double getPointValue(TickerDto ticker) {
                    CommodityDto commodity = (CommodityDto)commodityMap.get(ticker.getCommodityId());
                    return commodity.getPointValue().doubleValue();
                }

                public byte getInstrumentType(TickerDto ticker) {
                    String type = ticker.getType();
                    return (byte)(type != null && type.contains("ETF") ? 5 : 2);
                }

                public String getDescriptions(TickerDto ticker) {
                    return "History data instrument";
                }

                public double getOrderSizeMultiplier(TickerDto ticker) {
                    CommodityDto commodity = (CommodityDto)commodityMap.get(ticker.getCommodityId());
                    return commodity.getOrderSizeMulti().doubleValue();
                }

                public double getOrderSizeStep(TickerDto ticker) {
                    CommodityDto commodity = (CommodityDto)commodityMap.get(ticker.getCommodityId());
                    return commodity.getOrderSizeStep() == null ? 0.0 : commodity.getOrderSizeStep().doubleValue();
                }
            }, new BatchProgressController(){
                final /* synthetic */ SQFuturesDataServlet this$0;
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
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getInstruments(), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)rawSymbols, (String)"add"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
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

    private void subscriptionCheck(String[] symbols, Map<String, TickerDto> tickerMap, boolean eod) throws Exception {
        for (String symbol : symbols) {
            TickerDto ticker = tickerMap.get(symbol);
            if (ticker == null) continue;
            if (eod) {
                if (HistoryDataSubscription.getInstance().isAllowedFuture(symbol, ticker.getMarketName(), true)) continue;
                throw new Exception(L.t((String)"Cannot add ticker '%s'. EOD data subscription not active.", (Object[])new Object[]{symbol}));
            }
            if (HistoryDataSubscription.getInstance().isAllowedFuture(symbol, ticker.getMarketName(), false)) continue;
            throw new Exception(L.t((String)"Cannot add ticker '%s'. Intraday data subscription not active.", (Object[])new Object[]{symbol}));
        }
    }

    private String onLookup(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        boolean searchInName = Boolean.parseBoolean(args.get("searchInName")[0]);
        boolean searchInTicker = Boolean.parseBoolean(args.get("searchInTicker")[0]);
        boolean onlyContFutures = Boolean.parseBoolean(args.get("onlyContFutures")[0]);
        boolean exactMatch = Boolean.parseBoolean(args.get("exact")[0]);
        if (!searchInName && !searchInTicker) {
            throw new Exception(L.t((String)"Search method not set.", (Object[])new Object[0]));
        }
        TickerFilterDto filter = new TickerFilterDto();
        filter.setExactMatch(searchInTicker && exactMatch);
        filter.setSearchInName(searchInName);
        filter.setSearchInTicker(searchInTicker);
        filter.setOnlyContFutures(onlyContFutures);
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
        List tickers = HistoryDataManager.get().getFuturesTickers(filter);
        tickers = tickers.stream().filter(t -> !t.getTicker().startsWith("@") || t.getAliasTickerId() != null).collect(Collectors.toList());
        response.put("tickers", (Object)new TickerDtoToJsonTransformer(TickerKind.FUTURES).toJson(tickers));
        response.put("success", (Object)L.t((String)"Data lookup.", (Object[])new Object[0]));
        return response.toString();
    }

    private String onUpdate() throws Exception {
        ArrayList stockSymbols = DataManager.listForSource((int)6);
        return this.performUpdate(stockSymbols);
    }

    private String onUpdateBr() throws Exception {
        ArrayList stockSymbols = DataManager.listForSource((int)6);
        LinkedList<DataInfo> bmfData = new LinkedList<DataInfo>();
        for (DataInfo dataInfo : stockSymbols) {
            String instrument = dataInfo.instrument;
            if (instrument == null || !instrument.endsWith("- BMF")) continue;
            bmfData.add(dataInfo);
        }
        return this.performUpdate(bmfData);
    }

    private String performUpdate(List<DataInfo> stockSymbols) throws Exception {
        JSONObject response = new JSONObject();
        if (stockSymbols.isEmpty()) {
            response.put("success", (Object)L.t((String)"No symbols to update.", (Object[])new Object[0]));
            return response.toString();
        }
        List<String> symbolList = stockSymbols.stream().map(i -> i.uSymbol).collect(Collectors.toList());
        TickerFilterDto filter = new TickerFilterDto();
        filter.setSearchInTicker(true);
        filter.setExactMatch(true);
        filter.setNames(symbolList.toArray(new String[0]));
        List recordsFromDb = HistoryDataManager.get().getFuturesTickers(filter);
        Map<String, TickerDto> recordsMap = recordsFromDb.stream().collect(Collectors.toMap(TickerDto::getTicker, i -> i));
        LinkedList<DataInfo> filteredInfos = new LinkedList<DataInfo>();
        for (DataInfo dataInfo : stockSymbols) {
            if (!this.isDownloadAllowed(dataInfo, recordsMap)) continue;
            filteredInfos.add(dataInfo);
        }
        DownloadDispatcher.get().updateHistoryData(filteredInfos, recordsMap);
        if (!stockSymbols.isEmpty() && filteredInfos.isEmpty()) {
            throw new RuntimeException(L.t((String)"You don't have subscriptions for requested data.", (Object[])new Object[0]));
        }
        response.put("success", (Object)L.t((String)"Update started.", (Object[])new Object[0]));
        return response.toString();
    }

    private boolean isDownloadAllowed(DataInfo dataInfo, Map<String, TickerDto> recordsMap) throws ClientProtocolException, IllegalStateException, NoSuchAlgorithmException, IOException, JDOMException, SQLException {
        String timeframe = dataInfo.timeframe;
        boolean eod = !timeframe.equals("M1");
        TickerDto ticker = recordsMap.get(dataInfo.uSymbol);
        return HistoryDataSubscription.getInstance().isAllowedFuture(dataInfo.uSymbol, ticker.getMarketName(), eod);
    }

    private String onVerifySubscription(Map<String, String[]> args) throws Exception {
        JSONObject response = new JSONObject();
        HistoryDataSubscription subscription = HistoryDataSubscription.getInstance();
        response.put("eodSubscriptionActive", subscription.isFuturesEODActive());
        response.put("minuteSubscriptionActive", subscription.isFuturesMinuteActive());
        response.put("freeFutures", (Object)subscription.getFreeFutures());
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
                DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)symbols[i]);
                if (dataInfo.source != 6 || dataInfo.sourceDataId != 0) continue;
                stockSymbols.add(dataInfo);
            }
            return this.performUpdate(stockSymbols);
        }
        catch (Exception e) {
            return SQFuturesDataServlet.apiErrorJSON((String)L.t((String)"Cannot update data.", (Object[])new Object[0]), (Throwable)e);
        }
    }
}

