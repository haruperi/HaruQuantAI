/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.broker.BrokerDto
 *  com.strategyquant.datalib.broker.BrokerManager
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.customData.CustomDataManager
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.instrument.InstrumentManager
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionElement
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.timezone.Timezone
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.XMLUtil
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.broker.BrokerDto;
import com.strategyquant.datalib.broker.BrokerManager;
import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.customData.CustomDataManager;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.instrument.InstrumentManager;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionElement;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.timezone.Timezone;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.MoneyManagementMethod;
import com.strategyquant.tradinglib.RiskManagementMethod;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.databank.DatabankViewsManager;
import com.strategyquant.tradinglib.engine.TradingEngine;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.engine.TradingSetupStatus;
import com.strategyquant.tradinglib.historyData.HistoryDataManager;
import com.strategyquant.tradinglib.historyData.SpecialSymbolsManager;
import com.strategyquant.tradinglib.moneymanagement.MoneyManagementMethodsList;
import com.strategyquant.tradinglib.project.CustomConfigs;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.riskmanagement.RiskManagementMethodsList;
import com.strategyquant.tradinglib.tradelist.TradelistTableColumnEntry;
import com.strategyquant.tradinglib.tradelist.TradelistTableView;
import com.strategyquant.tradinglib.tradelist.TradelistViewsManager;
import java.util.ArrayList;
import java.util.Collection;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WSDataObjects {
    private static final Logger Log = LoggerFactory.getLogger(WSDataObjects.class);

    public static DataToSend getStrategies() {
        JSONArray jSONArray = new JSONArray();
        for (TradingSetup tradingSetup : TradingEngine.getLiveEngine().getTradingSetups()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("SetupID", tradingSetup.getSetupId());
            jSONObject.put("StrategyName", (Object)tradingSetup.getStrategy().getStrategyName());
            jSONObject.put("ConnectionName", (Object)tradingSetup.getChartSetup().getCharts().get(0).getConnectionName());
            jSONObject.put("Symbol", (Object)tradingSetup.getChartSetup().getCharts().get(0).getSymbol());
            jSONObject.put("Status", (Object)L.tsq((String)TradingSetupStatus.toString(tradingSetup.getStatus())));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("strategies", jSONArray);
    }

    public static DataToSend getConnections() {
        ConnectionManager connectionManager = TradingEngine.getLiveEngine().getConnectionManager();
        JSONArray jSONArray = new JSONArray();
        for (Connection connection : connectionManager.getAllConnections()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("ConnectionPlugin", (Object)connection.getPluginName());
            jSONObject.put("ConnectionName", (Object)connection.getConnectionName());
            jSONObject.put("ConnectionState", (Object)connection.getStatus());
            jSONObject.put("ConnectionParams", (Object)connection.getConnectionParams().toJSON());
            jSONObject.put("ConnectionType", (Object)connection.getType());
            if (connection.isExecutionEngine()) {
                jSONObject.put("OpenPositions", connection.getExecutionEngine().getOpenOrdersCount(false));
                jSONObject.put("AccountBalance", connection.getExecutionEngine().getAccountBalance());
                jSONObject.put("AccountPL", connection.getExecutionEngine().getTotalPL());
            } else {
                jSONObject.put("OpenPositions", (Object)"N/A");
                jSONObject.put("AccountBalance", (Object)"N/A");
                jSONObject.put("AccountPL", (Object)"N/A");
            }
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("connections", jSONArray);
    }

    public static DataToSend getDataForSingleSymbol(String string, String string2) throws Exception {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)string);
        try {
            JSONObject jSONObject2 = new JSONObject();
            jSONObject2.put("symbol", (Object)dataInfo.symbol);
            jSONObject2.put("barType", dataInfo.barTimeType);
            jSONObject2.put("dateFrom", dataInfo.dateFrom);
            jSONObject2.put("dateTo", dataInfo.dateTo);
            jSONObject2.put("rows", dataInfo.rows);
            jSONObject2.put("totalDays", SQTime.getDaysBetween((long)dataInfo.dateFrom, (long)dataInfo.dateTo));
            jSONObject2.put("connection", (Object)dataInfo.connection);
            jSONObject2.put("filename", (Object)dataInfo.filename);
            jSONObject2.put("instrument", (Object)dataInfo.instrument);
            jSONObject2.put("timeframe", (Object)dataInfo.timeframe);
            jSONObject2.put("timezone", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)false));
            jSONObject2.put("timezoneShort", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)true));
            jSONObject2.put("source", dataInfo.source);
            jSONObject2.put("secondsRecords", dataInfo.secondsRecords);
            InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument);
            jSONObject2.put("pointValue", instrumentInfo.pointValue);
            jSONObject2.put("tickSize", instrumentInfo.tickSize);
            jSONObject2.put("tickStep", instrumentInfo.tickStep);
            jSONObject2.put("dataType", instrumentInfo.dataType);
            jSONObject2.put("spread", instrumentInfo.defaultSpread);
            jSONObject2.put("slippage", instrumentInfo.defaultSlippage);
            jSONObject2.put("commissions", (Object)instrumentInfo.commissions);
            jSONObject2.put("swap", (Object)instrumentInfo.swap);
            jSONObject2.put("uSymbol", (Object)dataInfo.uSymbol);
            jSONObject2.put("uSymbolName", (Object)dataInfo.uSymbolName);
            jSONObject2.put("id", dataInfo.id);
            jSONObject2.put("sourceDataId", dataInfo.sourceDataId);
            jSONObject2.put("show", dataInfo.show);
            jSONArray.put((Object)jSONObject2);
        }
        catch (Exception exception) {
            Log.error("Cannot load symbol. Exc.", (Throwable)exception);
            Log.error("Deleting symbol " + dataInfo.symbol, (Throwable)exception);
            DataManager.deleteData((String)dataInfo.connection, (String)dataInfo.symbol);
        }
        jSONObject.put("action", (Object)string2);
        jSONObject.put("symbols", (Object)string);
        jSONObject.put("data", (Object)jSONArray);
        return new DataToSend("data", jSONObject);
    }

    public static DataToSend getData(String string, String string2) throws Exception {
        List list;
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        Map<String, BasketDto> map = null;
        BasketOfStocksManager basketOfStocksManager = BasketOfStocksManager.getInstance();
        if (basketOfStocksManager != null) {
            list = BasketOfStocksManager.getInstance().getGroups();
            map = list.stream().collect(Collectors.toMap(BasketDto::getName, basketDto -> basketDto));
        }
        list = DataManager.list();
        HashMap<String, DataInfo> hashMap = new HashMap<String, DataInfo>();
        HashSet<String> hashSet = new HashSet<String>();
        for (DataInfo dataInfo : list) {
            hashSet.add(dataInfo.symbol);
            hashMap.put(dataInfo.symbol, dataInfo);
        }
        for (DataInfo dataInfo : list) {
            if (SpecialSymbolsManager.isSpecial(dataInfo)) continue;
            try {
                Object object;
                JSONObject jSONObject2 = new JSONObject();
                jSONObject2.put("symbol", (Object)dataInfo.symbol);
                jSONObject2.put("barType", dataInfo.barTimeType);
                jSONObject2.put("dateFrom", dataInfo.dateFrom);
                jSONObject2.put("dateTo", dataInfo.dateTo);
                jSONObject2.put("rows", dataInfo.rows);
                jSONObject2.put("totalDays", SQTime.getDaysBetween((long)dataInfo.dateFrom, (long)dataInfo.dateTo));
                jSONObject2.put("connection", (Object)dataInfo.connection);
                jSONObject2.put("filename", (Object)dataInfo.filename);
                jSONObject2.put("instrument", (Object)dataInfo.instrument);
                jSONObject2.put("timeframe", (Object)dataInfo.timeframe);
                jSONObject2.put("timezone", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)false));
                jSONObject2.put("timezoneShort", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)true));
                jSONObject2.put("source", dataInfo.source);
                jSONObject2.put("secondsRecords", dataInfo.secondsRecords);
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument);
                jSONObject2.put("pointValue", instrumentInfo.pointValue);
                jSONObject2.put("tickSize", instrumentInfo.tickSize);
                jSONObject2.put("tickStep", instrumentInfo.tickStep);
                jSONObject2.put("dataType", instrumentInfo.dataType);
                jSONObject2.put("spread", instrumentInfo.defaultSpread);
                jSONObject2.put("slippage", instrumentInfo.defaultSlippage);
                jSONObject2.put("commissions", (Object)instrumentInfo.commissions);
                jSONObject2.put("swap", (Object)instrumentInfo.swap);
                jSONObject2.put("uSymbol", (Object)dataInfo.uSymbol);
                jSONObject2.put("uSymbolName", (Object)dataInfo.uSymbolName);
                jSONObject2.put("id", dataInfo.id);
                jSONObject2.put("sourceDataId", dataInfo.sourceDataId);
                jSONObject2.put("show", dataInfo.show);
                jSONObject2.put("broker", dataInfo.brokerId);
                jSONObject2.put("brokerName", (Object)BrokerManager.getInstance().getBrokerName(dataInfo.brokerId));
                boolean bl = true;
                if (basketOfStocksManager != null && dataInfo.symbol.startsWith("[") && (object = map.get(dataInfo.symbol)) != null) {
                    int n = BasketOfStocksManager.getDownloaded(hashMap, (Integer)object.getId());
                    bl = BasketOfStocksManager.isReadyForUse((int)n, (int)object.getTotal());
                }
                jSONObject2.put("readyToUse", bl);
                object = null;
                if (dataInfo.source == 5) {
                    object = HistoryDataManager.get().getStockExchange(dataInfo.uSymbol);
                } else if (dataInfo.source == 6) {
                    object = HistoryDataManager.get().getFuturesExchange(dataInfo.uSymbol);
                }
                jSONObject2.put("exchange", (Object)(object == null ? "" : object));
                jSONArray.put((Object)jSONObject2);
            }
            catch (Exception exception) {
                Log.error("Cannot load symbol. Exc.", (Throwable)exception);
                Log.error("Deleting symbol " + dataInfo.symbol, (Throwable)exception);
                DataManager.deleteData((String)dataInfo.connection, (String)dataInfo.symbol);
            }
        }
        jSONObject.put("action", (Object)string2);
        jSONObject.put("symbols", (Object)string);
        jSONObject.put("data", (Object)jSONArray);
        return new DataToSend("data", jSONObject);
    }

    public static DataToSend getData(Set<String> set, String string, String string2) throws Exception {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        ArrayList arrayList = DataManager.list();
        for (DataInfo dataInfo : arrayList) {
            try {
                if (!set.contains(dataInfo.symbol)) continue;
                JSONObject jSONObject2 = new JSONObject();
                jSONObject2.put("symbol", (Object)dataInfo.symbol);
                jSONObject2.put("barType", dataInfo.barTimeType);
                jSONObject2.put("dateFrom", dataInfo.dateFrom);
                jSONObject2.put("dateTo", dataInfo.dateTo);
                jSONObject2.put("rows", dataInfo.rows);
                jSONObject2.put("totalDays", SQTime.getDaysBetween((long)dataInfo.dateFrom, (long)dataInfo.dateTo));
                jSONObject2.put("connection", (Object)dataInfo.connection);
                jSONObject2.put("filename", (Object)dataInfo.filename);
                jSONObject2.put("instrument", (Object)dataInfo.instrument);
                jSONObject2.put("timeframe", (Object)dataInfo.timeframe);
                jSONObject2.put("timezone", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)false));
                jSONObject2.put("timezoneShort", (Object)Timezone.print((String)dataInfo.timezone, (int)dataInfo.source, (boolean)true));
                jSONObject2.put("source", dataInfo.source);
                jSONObject2.put("secondsRecords", dataInfo.secondsRecords);
                InstrumentInfo instrumentInfo = InstrumentManager.getInstrumentInfo((String)dataInfo.instrument);
                jSONObject2.put("pointValue", instrumentInfo.pointValue);
                jSONObject2.put("tickSize", instrumentInfo.tickSize);
                jSONObject2.put("tickStep", instrumentInfo.tickStep);
                jSONObject2.put("dataType", instrumentInfo.dataType);
                jSONObject2.put("spread", instrumentInfo.defaultSpread);
                jSONObject2.put("slippage", instrumentInfo.defaultSlippage);
                jSONObject2.put("commissions", (Object)instrumentInfo.commissions);
                jSONObject2.put("swap", (Object)instrumentInfo.swap);
                jSONObject2.put("uSymbol", (Object)dataInfo.uSymbol);
                jSONObject2.put("uSymbolName", (Object)dataInfo.uSymbolName);
                jSONObject2.put("id", dataInfo.id);
                jSONObject2.put("sourceDataId", dataInfo.sourceDataId);
                jSONObject2.put("show", dataInfo.show);
                jSONArray.put((Object)jSONObject2);
            }
            catch (Exception exception) {
                Log.error("Cannot load symbol. Exc.", (Throwable)exception);
                Log.error("Deleting symbol " + dataInfo.symbol, (Throwable)exception);
                DataManager.deleteData((String)dataInfo.connection, (String)dataInfo.symbol);
            }
        }
        jSONObject.put("action", (Object)string2);
        jSONObject.put("symbols", (Object)string);
        jSONObject.put("data", (Object)jSONArray);
        return new DataToSend("data", jSONObject);
    }

    public static DataToSend getCustomData(String string, String string2) throws Exception {
        JSONObject jSONObject = new JSONObject();
        JSONArray jSONArray = new JSONArray();
        Collection collection = CustomDataManager.list();
        for (CustomDataInfo customDataInfo : collection) {
            try {
                JSONObject jSONObject2 = new JSONObject();
                jSONObject2.put("id", customDataInfo.id);
                jSONObject2.put("name", (Object)customDataInfo.name);
                jSONObject2.put("dataType", customDataInfo.dataType);
                jSONObject2.put("values", customDataInfo.values);
                jSONObject2.put("valuesObject", (Object)customDataInfo.valuesObject);
                jSONObject2.put("timeframe", (Object)customDataInfo.timeframe);
                jSONObject2.put("rows", customDataInfo.rows);
                jSONObject2.put("dateFrom", customDataInfo.dateFrom);
                jSONObject2.put("dateTo", customDataInfo.dateTo);
                jSONObject2.put("totalDays", SQTime.getDaysBetween((long)customDataInfo.dateFrom, (long)customDataInfo.dateTo));
                jSONObject2.put("filename", (Object)customDataInfo.filename);
                jSONObject2.put("timeframe", (Object)customDataInfo.timeframe);
                jSONArray.put((Object)jSONObject2);
            }
            catch (Exception exception) {
                Log.error("Cannot load custom data. Exc.", (Throwable)exception);
            }
        }
        jSONObject.put("action", (Object)string2);
        jSONObject.put("names", (Object)string);
        jSONObject.put("data", (Object)jSONArray);
        return new DataToSend("customdata", jSONObject);
    }

    public static DataToSend getBaskets() {
        ArrayList arrayList;
        JSONArray jSONArray = new JSONArray();
        List list = BasketOfStocksManager.getInstance().getGroups();
        try {
            DataManager.get();
            arrayList = DataManager.list();
        }
        catch (Exception exception) {
            throw new RuntimeException(L.t((String)"Error while fetching list of symbols", (Object[])new Object[0]), exception);
        }
        HashMap<String, DataInfo> hashMap = new HashMap<String, DataInfo>();
        HashSet<String> hashSet = new HashSet<String>();
        for (DataInfo dataInfo : arrayList) {
            hashSet.add(dataInfo.symbol);
            hashMap.put(dataInfo.symbol, dataInfo);
        }
        for (DataInfo dataInfo : list) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("id", (Object)dataInfo.getId());
            jSONObject.put("name", (Object)dataInfo.getName());
            jSONObject.put("count", dataInfo.getCount());
            jSONObject.put("desc", (Object)dataInfo.getDesc());
            List list2 = BasketOfStocksManager.getInstance().getStocks(dataInfo.getId().intValue());
            List list3 = list2.stream().map(StockDto::getTicker).collect(Collectors.toList());
            jSONObject.put("stocks", (Object)("," + String.join((CharSequence)",", list3) + ","));
            jSONObject.put("existingSymbols", BasketOfStocksManager.getNumberOfSymbolsInGroup(hashSet, (BasketDto)dataInfo));
            int n = BasketOfStocksManager.getDownloaded(hashMap, (Integer)dataInfo.getId());
            jSONObject.put("downloadedInfo", (Object)(n + " / " + dataInfo.getTotal()));
            jSONObject.put("readyToUse", BasketOfStocksManager.isReadyForUse((int)n, (int)dataInfo.getTotal()));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("baskets", jSONArray);
    }

    public static DataToSend getBrokers() {
        JSONArray jSONArray = new JSONArray();
        List list = BrokerManager.getInstance().getAllBrokers();
        for (BrokerDto brokerDto : list) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("id", (Object)brokerDto.getId());
            jSONObject.put("name", (Object)brokerDto.getName());
            jSONObject.put("customizedStocks", brokerDto.getCustomizedStocks());
            jSONObject.put("desc", (Object)brokerDto.getDesc());
            jSONObject.put("stockPickerUse", brokerDto.isStockPickerUse());
            jSONObject.put("mtUse", brokerDto.isMtUse());
            jSONObject.put("postfix", (Object)brokerDto.getPostfix());
            jSONObject.put("mtTimezone", (Object)brokerDto.getMtTimezone());
            List list2 = BrokerManager.getInstance().getStocks(brokerDto.getId().intValue());
            jSONObject.put("stocks", (Object)("," + String.join((CharSequence)",", list2) + ","));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("brokers", jSONArray);
    }

    public static DataToSend getInstruments() throws DataException {
        JSONArray jSONArray = new JSONArray();
        ArrayList arrayList = InstrumentManager.list();
        for (InstrumentInfo instrumentInfo : arrayList) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("defaultSpread", instrumentInfo.defaultSpread);
            jSONObject.put("defaultSlippage", instrumentInfo.defaultSlippage);
            jSONObject.put("pointValue", instrumentInfo.pointValue);
            jSONObject.put("commissions", (Object)instrumentInfo.commissions);
            jSONObject.put("decimals", instrumentInfo.decimals);
            jSONObject.put("tickSize", instrumentInfo.tickSize);
            jSONObject.put("tickStep", instrumentInfo.tickStep);
            jSONObject.put("tickValueInMoney", instrumentInfo.tickValueInMoney);
            jSONObject.put("description", (Object)instrumentInfo.description);
            jSONObject.put("instrument", (Object)instrumentInfo.instrument);
            jSONObject.put("dataType", instrumentInfo.dataType);
            jSONObject.put("exchange", (Object)instrumentInfo.exchange);
            jSONObject.put("country", (Object)instrumentInfo.country);
            jSONObject.put("sector", (Object)instrumentInfo.sector);
            jSONObject.put("swap", (Object)instrumentInfo.swap);
            jSONObject.put("minDistance", instrumentInfo.minDistance);
            jSONObject.put("broker", instrumentInfo.broker);
            jSONObject.put("orderSizeMultiplier", instrumentInfo.orderSizeMultiplier);
            jSONObject.put("orderSizeStep", instrumentInfo.orderSizeStep);
            JSONArray jSONArray2 = new JSONArray();
            jSONObject.put("aliases", (Object)jSONArray2);
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("instruments", jSONArray);
    }

    public static DataToSend getAliases() throws DataException {
        JSONArray jSONArray = new JSONArray();
        return new DataToSend("aliases", jSONArray);
    }

    public static DataToSend getSessions() throws Exception {
        JSONArray jSONArray = new JSONArray();
        for (Session session : SessionManager.getSessions()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)session.getSessionName());
            jSONObject.put("broker", session.getBroker());
            jSONObject.put("brokerName", (Object)BrokerManager.getInstance().getBrokerName(session.getBroker()));
            try {
                JSONArray jSONArray2 = new JSONArray();
                if (session.getElements() != null) {
                    for (SessionElement sessionElement : session.getElements()) {
                        JSONObject jSONObject2 = new JSONObject();
                        jSONObject2.put("dayFrom", (Object)sessionElement.getDayFromStr());
                        jSONObject2.put("timeFrom", (Object)sessionElement.getTimeFromStr());
                        jSONObject2.put("dayTo", (Object)sessionElement.getDayToStr());
                        jSONObject2.put("timeTo", (Object)sessionElement.getTimeToStr());
                        jSONObject2.put("eod", sessionElement.isEOD());
                        jSONArray2.put((Object)jSONObject2);
                    }
                }
                jSONObject.put("elements", (Object)jSONArray2);
                jSONArray.put((Object)jSONObject);
            }
            catch (Exception exception) {
                Log.error("Cannot load session", (Throwable)exception);
            }
        }
        return new DataToSend("sessions", jSONArray);
    }

    public static DataToSend getTimeframes() {
        return WSDataObjects.getTimeframes(true);
    }

    public static DataToSend getTimeframes(boolean bl) {
        JSONArray jSONArray = new JSONArray();
        for (String string : TimeframeManager.getTimeframes()) {
            if (!bl && "TICK".equals(string)) continue;
            jSONArray.put((Object)string);
        }
        return new DataToSend("timeframes", jSONArray);
    }

    public static DataToSend getExchanges() {
        JSONArray jSONArray = new JSONArray();
        for (String string : InstrumentManager.getExchanges()) {
            jSONArray.put((Object)string);
        }
        return new DataToSend("exchanges", jSONArray);
    }

    public static DataToSend getCountries() {
        JSONArray jSONArray = new JSONArray();
        for (String string : InstrumentManager.getCountries()) {
            jSONArray.put((Object)string);
        }
        return new DataToSend("countries", jSONArray);
    }

    public static DataToSend getSectors() {
        JSONArray jSONArray = new JSONArray();
        for (String string : InstrumentManager.getSectors()) {
            jSONArray.put((Object)string);
        }
        return new DataToSend("sectors", jSONArray);
    }

    public static DataToSend getTradelistViews() {
        JSONArray jSONArray = new JSONArray();
        for (String string : TradelistViewsManager.getInstance().getViews().keySet()) {
            TradelistTableView tradelistTableView;
            JSONObject jSONObject = new JSONObject();
            JSONArray jSONArray2 = new JSONArray();
            try {
                tradelistTableView = TradelistViewsManager.getInstance().getView(string);
            }
            catch (Exception exception) {
                Log.error("Cannot load view '" + string + "'. ", (Throwable)exception);
                continue;
            }
            jSONObject.put("name", (Object)string);
            for (TradelistTableColumnEntry tradelistTableColumnEntry : tradelistTableView.columns) {
                try {
                    JSONObject jSONObject2 = new JSONObject();
                    jSONObject2.put("entryName", (Object)tradelistTableColumnEntry.getColumnEntryName());
                    jSONObject2.put("columnName", (Object)tradelistTableColumnEntry.tableColumn.getName());
                    jSONObject2.put("class", (Object)tradelistTableColumnEntry.tableColumn.getClass().getSimpleName());
                    jSONObject2.put("width", tradelistTableColumnEntry.tableColumn.getWidth());
                    jSONObject2.put("type", (Object)tradelistTableColumnEntry.tableColumn.getType());
                    jSONObject2.put("fontBold", tradelistTableColumnEntry.tableColumn.isFontBold());
                    jSONArray2.put((Object)jSONObject2);
                }
                catch (Exception exception) {
                    Log.error("Cannot load columns of view '" + string + "'. ", (Throwable)exception);
                }
            }
            jSONObject.put("columns", (Object)jSONArray2);
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("tradelistViews", jSONArray);
    }

    public static DataToSend getDatabankViews() {
        return new DataToSend("databankViews", DatabankViewsManager.getInstance().toJSON());
    }

    public static DataToSend getMMMethods() {
        JSONArray jSONArray = new JSONArray();
        for (MoneyManagementMethod moneyManagementMethod : MoneyManagementMethodsList.get().getAvailableClasses()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("engine", (Object)moneyManagementMethod.getEngine());
            jSONObject.put("name", (Object)moneyManagementMethod.getName());
            jSONObject.put("help", (Object)moneyManagementMethod.getNote());
            jSONObject.put("description", (Object)moneyManagementMethod.getDescription());
            jSONObject.put("class", (Object)moneyManagementMethod.getClass().getSimpleName());
            jSONObject.put("config", (Object)XMLUtil.elementToString((Element)moneyManagementMethod.getXML()));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("mmMethods", jSONArray);
    }

    public static DataToSend getRMMethods() {
        JSONArray jSONArray = new JSONArray();
        for (RiskManagementMethod riskManagementMethod : RiskManagementMethodsList.get().getAvailableClasses()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)riskManagementMethod.getName());
            jSONObject.put("help", (Object)riskManagementMethod.getNote());
            jSONObject.put("class", (Object)riskManagementMethod.getClass().getSimpleName());
            jSONObject.put("config", (Object)XMLUtil.elementToString((Element)riskManagementMethod.getXML()));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("rmMethods", jSONArray);
    }

    public static DataToSend getTaskTemplates() {
        JSONArray jSONArray = new JSONArray();
        HashMap<String, String> hashMap = CustomConfigs.list();
        for (String string : hashMap.keySet()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)string);
            jSONObject.put("project", (Object)hashMap.get(string));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("taskConfigs", jSONArray);
    }

    public static DataToSend getTradingOptions() {
        JSONArray jSONArray = new JSONArray();
        HashMap<String, String> hashMap = CustomConfigs.list();
        for (String string : hashMap.keySet()) {
            JSONObject jSONObject = new JSONObject();
            jSONObject.put("name", (Object)string);
            jSONObject.put("project", (Object)hashMap.get(string));
            jSONArray.put((Object)jSONObject);
        }
        return new DataToSend("taskConfigs", jSONArray);
    }
}

