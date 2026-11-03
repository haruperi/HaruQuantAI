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
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.pluginlib.annotations.Category
 *  com.strategyquant.pluginlib.annotations.License
 *  com.strategyquant.pluginlib.annotations.Name
 *  com.strategyquant.pluginlib.annotations.ShortDesc
 *  com.strategyquant.tradinglib.exchange.Exchange
 *  com.strategyquant.tradinglib.exchange.IExchange
 *  com.strategyquant.tradinglib.exchange.SymbolInfo
 *  com.strategyquant.tradinglib.historyData.HttpApacheManager
 *  net.xeoh.plugins.base.annotations.PluginImplementation
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.CryptoExchange.impl.Bitfinex;

import com.fasterxml.jackson.core.JsonFactory;
import com.fasterxml.jackson.core.JsonParser;
import com.fasterxml.jackson.core.JsonToken;
import com.strategyquant.datalib.TimeframeManager;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.pluginlib.annotations.Category;
import com.strategyquant.pluginlib.annotations.License;
import com.strategyquant.pluginlib.annotations.Name;
import com.strategyquant.pluginlib.annotations.ShortDesc;
import com.strategyquant.tradinglib.exchange.Exchange;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.exchange.SymbolInfo;
import com.strategyquant.tradinglib.historyData.HttpApacheManager;
import java.io.IOException;
import java.math.BigDecimal;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Takacs")
@Name(name="Bitfinex")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for managing Bitfinex data")
@PluginImplementation
public class CryptoExchangeBitfinexPlugin
extends Exchange {
    private JSONArray availableSymbols = null;

    public String getName() {
        return "Bitfinex";
    }

    public JSONArray getSymbols() throws Exception {
        if (this.availableSymbols != null) {
            return this.availableSymbols;
        }
        String response = new String(HttpApacheManager.getInstance().getData("https://api.bitfinex.com/v2/conf/pub:list:pair:exchange"));
        this.availableSymbols = new JSONArray(response).getJSONArray(0);
        return this.availableSymbols;
    }

    public IExchange clone() {
        return new CryptoExchangeBitfinexPlugin();
    }

    public void download() throws Exception {
        String response = null;
        long timeframeMs = TimeframeManager.getMillis((String)this.dataInfo.timeframe);
        String timeframe = this.convertTimeframe(this.dataInfo.timeframe);
        long startTime = this.importInfo.dateFrom > 0L ? this.importInfo.dateFrom : 0L;
        startTime = this.dataMerger.checkDate(startTime);
        JsonFactory jfactory = new JsonFactory();
        while (startTime <= this.importInfo.dateTo) {
            String link = "https://api.bitfinex.com/v2/candles/trade:" + timeframe + ":t" + this.dataInfo.uSymbol + "/hist?limit=10000&sort=1&start=" + startTime;
            long startPerformed = this.dataMerger.getPerformedDays();
            long startCycleTime = System.currentTimeMillis();
            this.dataMerger.register(0, startTime / 1000L);
            this.dataMerger.reset(1);
            response = this.doDownload(link);
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
            startTime = data.time;
            startTime += timeframeMs;
            if (this.canceled && !this.stopping) {
                this.importInfo.dateTo = SQTime.correctDayEnd((long)startTime);
                this.stopping = true;
            }
            this.checkPaused();
            this.evaluateSpeed(startCycleTime, startPerformed, response.getBytes().length, downloadedDuration);
            Thread.sleep(2000L);
            if (this.dataMerger.getReader() == null) continue;
            this.dataMerger.readTill(startTime, false);
        }
    }

    private VersatileData parseData(JSONArray jsonArray) {
        VersatileData data = new VersatileData();
        data.time = jsonArray.getLong(0);
        data.open = jsonArray.getDouble(1);
        data.close = jsonArray.getDouble(2);
        data.high = jsonArray.getDouble(3);
        data.low = jsonArray.getDouble(4);
        data.volume = jsonArray.getDouble(5);
        return data;
    }

    private VersatileData parseData2(JsonParser jParser) throws IOException {
        VersatileData data = new VersatileData();
        data.time = jParser.nextLongValue(-1L);
        jParser.nextValue();
        data.open = jParser.getNumberValue().doubleValue();
        jParser.nextValue();
        data.close = jParser.getNumberValue().doubleValue();
        jParser.nextValue();
        data.high = jParser.getNumberValue().doubleValue();
        jParser.nextValue();
        data.low = jParser.getNumberValue().doubleValue();
        jParser.nextValue();
        data.volume = jParser.getNumberValue().doubleValue();
        return data;
    }

    public JSONArray availableTimeframes() {
        return new JSONArray().put((Object)"M1").put((Object)"M5").put((Object)"M15").put((Object)"M30").put((Object)"H1").put((Object)"H3").put((Object)"H6").put((Object)"H12").put((Object)"D1");
    }

    public String convertTimeframe(String tf) throws Exception {
        String prefix = tf.substring(0, 1);
        int count = 0;
        try {
            count = Integer.parseInt(tf.substring(1));
        }
        catch (Exception e) {
            throw new Exception(L.t((String)"Invalid timeframe format. Cannot parse time units count.", (Object[])new Object[0]));
        }
        switch (prefix) {
            case "M": {
                return count + "m";
            }
            case "H": {
                return count + "h";
            }
            case "D": {
                return count + "D";
            }
        }
        throw new Exception(L.t((String)"Invalid timeframe format. Prefix '%s' not recognized.", (Object[])new Object[]{prefix}));
    }

    public boolean checkSymbolExists(String symbol) {
        try {
            String response = SQUtils.httpGet((String)("https://api.bitfinex.com/v1/pubticker/" + symbol));
            JSONObject object = new JSONObject(response);
            object.getString("last_price");
        }
        catch (Exception e) {
            return false;
        }
        return true;
    }

    public SymbolInfo getSymbolInfo(String symbol) {
        try {
            String response = SQUtils.httpGet((String)"https://api.bitfinex.com/v1/symbols_details");
            JSONArray arr = new JSONArray(response);
            SymbolInfo symbolInfo = new SymbolInfo();
            for (int i = 0; i < arr.length(); ++i) {
                JSONObject iInfo = arr.getJSONObject(i);
                String iSymbol = iInfo.getString("pair");
                if (!symbol.equalsIgnoreCase(iSymbol)) continue;
                int pricePrecision = iInfo.getInt("price_precision");
                double value = BigDecimal.ONE.movePointLeft(pricePrecision).doubleValue();
                symbolInfo.setTickSize(value);
                symbolInfo.setTickStep(value);
                break;
            }
            return symbolInfo;
        }
        catch (Exception e) {
            throw new RuntimeException("Error while fetching symbol info", e);
        }
    }
}

