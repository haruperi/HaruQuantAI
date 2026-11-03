/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.fasterxml.jackson.core.JsonFactory
 *  com.fasterxml.jackson.core.JsonParser
 *  com.fasterxml.jackson.core.JsonToken
 *  com.strategyquant.datalib.TimeframeManager
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.exchange.Exchange
 *  com.strategyquant.tradinglib.exchange.IExchange
 *  com.strategyquant.tradinglib.exchange.SymbolInfo
 *  com.strategyquant.tradinglib.historyData.HttpApacheManager
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  org.apache.http.client.ClientProtocolException
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.CryptoExchange.impl.BinanceUsdtM;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.exchange.Exchange;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.exchange.SymbolInfo;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import org.apache.http.client.ClientProtocolException;
import org.json.JSONArray;
import org.json.JSONObject;

@Name(name="BinanceUsdtM")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for managing Binance Usd-M data")
@PluginImplementation
public class CryptoExchangeBinanceUsdtMPlugin
extends Exchange {
    private static final long MAX_BARS_PER_REQUEST = 1500L;
    private static final long MAX_RANGE_MS = Duration.ofDays(200L).toMillis();
    private String exchangeInfo;
    private JSONArray availableSymbols = null;

    public String getName() {
        return "Binance USDT-M";
    }

    public JSONArray getSymbols() throws Exception {
        if (this.availableSymbols != null) {
            return this.availableSymbols;
        }
        JSONArray symbols = new JSONArray();
        String response = new String(HttpApacheManager.getInstance().getData("https://fapi.binance.com/fapi/v1/exchangeInfo"), StandardCharsets.UTF_8);
        JSONObject obj = new JSONObject(response);
        JSONArray array = obj.getJSONArray("symbols");
        for (int i = 0; i < array.length(); ++i) {
            String ticker = array.getJSONObject(i).getString("symbol");
            boolean isAscii = ticker.chars().allMatch(ch -> ch < 128);
            if (!isAscii) continue;
            symbols.put((Object)ticker);
        }
        this.availableSymbols = symbols;
        return this.availableSymbols;
    }

    public IExchange clone() {
        return new CryptoExchangeBinanceUsdtMPlugin();
    }

    private String getStartEndParams(long startTime, long endTime) {
        if (endTime >= System.currentTimeMillis()) {
            return "startTime=" + startTime;
        }
        return "startTime=" + startTime + "&endTime=" + endTime;
    }

    public void download() throws Exception {
        long timeframeMs = TimeframeManager.getMillis((String)this.dataInfo.timeframe);
        String timeframe = this.convertTimeframe(this.dataInfo.timeframe);
        int idx = 0;
        long startTime = this.importInfo.dateFrom > 0L ? this.importInfo.dateFrom : this.getSymbolInfo(this.dataInfo.uSymbol).getDateFrom();
        startTime = this.dataMerger.checkDate(startTime);
        long requestedRange = 1500L * timeframeMs;
        long cappedRange = Math.min(requestedRange, MAX_RANGE_MS);
        JsonFactory jfactory = new JsonFactory();
        while (startTime <= this.importInfo.dateTo) {
            long endTime = startTime + cappedRange;
            String link = "https://fapi.binance.com/fapi/v1/klines?symbol=" + this.dataInfo.uSymbol + "&interval=" + timeframe + "&limit=1500&" + this.getStartEndParams(startTime, endTime);
            long startPerformed = this.dataMerger.getPerformedDays();
            long startCycleTime = System.currentTimeMillis();
            this.dataMerger.register(0, startTime / 1000L);
            this.dataMerger.reset(1);
            String response = this.doDownload(link);
            long downloadedDuration = System.currentTimeMillis() - startCycleTime;
            JsonParser jParser = jfactory.createParser(response);
            jParser.nextToken();
            VersatileData data = null;
            while (jParser.currentToken() != null) {
                jParser.nextToken();
                if (jParser.currentToken() == JsonToken.END_ARRAY) break;
                data = this.parseData2(jParser);
                if (data.time > this.importInfo.dateTo) break;
                this.dataMerger.storeToQueue(0, data);
                jParser.nextToken();
            }
            if (data == null) break;
            this.dataMerger.tryToSaveQueue(startTime);
            startTime = data.time + timeframeMs;
            this.checkPaused();
            if (this.canceled && !this.stopping) {
                this.importInfo.dateTo = SQTime.correctDayEnd((long)startTime);
                this.stopping = true;
            }
            this.evaluateSpeed(startCycleTime, startPerformed, response.getBytes().length, downloadedDuration);
            if (++idx % 25 == 0) {
                Thread.sleep(2000L);
            }
            if (this.dataMerger.getReader() == null) continue;
            this.dataMerger.readTill(startTime, false);
        }
    }

    private VersatileData parseData2(JsonParser jParser) throws IOException {
        VersatileData data = new VersatileData();
        data.time = jParser.nextLongValue(-1L);
        data.open = Double.valueOf(jParser.nextTextValue());
        data.high = Double.valueOf(jParser.nextTextValue());
        data.low = Double.valueOf(jParser.nextTextValue());
        data.close = Double.valueOf(jParser.nextTextValue());
        data.volume = Double.valueOf(jParser.nextTextValue());
        jParser.nextToken();
        jParser.nextToken();
        jParser.nextToken();
        jParser.nextToken();
        jParser.nextToken();
        jParser.nextToken();
        return data;
    }

    private VersatileData parseData(JSONArray jsonArray) {
        VersatileData data = new VersatileData();
        data.time = jsonArray.getLong(0);
        data.open = jsonArray.getDouble(1);
        data.high = jsonArray.getDouble(2);
        data.low = jsonArray.getDouble(3);
        data.close = jsonArray.getDouble(4);
        data.volume = jsonArray.getDouble(5);
        return data;
    }

    public JSONArray availableTimeframes() {
        return new JSONArray().put((Object)"M1").put((Object)"M3").put((Object)"M5").put((Object)"M15").put((Object)"M30").put((Object)"H1").put((Object)"H2").put((Object)"H4").put((Object)"H6").put((Object)"H8").put((Object)"H12").put((Object)"D1");
    }

    public String convertTimeframe(String tf) throws Exception {
        String prefix = tf.substring(0, 1);
        int count = 0;
        try {
            count = Integer.parseInt(tf.substring(1));
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Invalid timeframe format. Cannot parse time units count.", (Object[])new Object[]{true}));
        }
        switch (prefix) {
            case "M": {
                return count + "m";
            }
            case "H": {
                return count + "h";
            }
            case "D": {
                return count + "d";
            }
        }
        throw new Exception(L.t((String)"Invalid timeframe format. Prefix '%s' not recognized.", (Object[])new Object[]{prefix}));
    }

    public boolean checkSymbolExists(String symbol) {
        return true;
    }

    private synchronized String getExchangeInfo() throws ClientProtocolException, IOException {
        if (this.exchangeInfo != null) {
            return this.exchangeInfo;
        }
        this.exchangeInfo = new String(HttpApacheManager.getInstance().getData("https://fapi.binance.com/fapi/v1/exchangeInfo"));
        return this.exchangeInfo;
    }

    public SymbolInfo getSymbolInfo(String symbol) {
        String response;
        try {
            response = this.getExchangeInfo();
        }
        catch (IOException e) {
            throw new RuntimeException("Error while fetching symbol info", e);
        }
        JSONObject object = new JSONObject(response);
        JSONArray symbols = object.getJSONArray("symbols");
        SymbolInfo symbolInfo = this.findSymbolInfo(symbols, symbol);
        return symbolInfo;
    }

    private SymbolInfo findSymbolInfo(JSONArray symbols, String symbol) {
        SymbolInfo symbolInfo = new SymbolInfo();
        for (int i = 0; i < symbols.length(); ++i) {
            JSONObject symbolJson = symbols.getJSONObject(i);
            if (!symbol.equals(symbolJson.getString("symbol"))) continue;
            this.fillSymbolInfo(symbolInfo, symbolJson);
            break;
        }
        return symbolInfo;
    }

    private void fillSymbolInfo(SymbolInfo symbolInfo, JSONObject symbolJson) {
        JSONArray filtersArray = symbolJson.getJSONArray("filters");
        for (int i = 0; i < filtersArray.length(); ++i) {
            JSONObject iFilter = filtersArray.getJSONObject(i);
            String filterType = iFilter.getString("filterType");
            if (!"PRICE_FILTER".equalsIgnoreCase(filterType)) continue;
            symbolInfo.setTickSize(Double.valueOf(iFilter.getString("tickSize")).doubleValue());
            symbolInfo.setTickStep(symbolInfo.getTickSize());
        }
        symbolInfo.setDateFrom(symbolJson.getLong("onboardDate"));
    }
}

