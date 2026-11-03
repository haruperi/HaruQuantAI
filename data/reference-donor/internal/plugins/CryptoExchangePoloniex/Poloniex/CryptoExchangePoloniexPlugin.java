/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
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
 *  net.xeoh.plugins.base.annotations.meta.Author
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.CryptoExchange.impl.Poloniex;

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
import java.math.BigDecimal;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Takacs")
@Name(name="Poloniex")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for managing Poloniex data")
@PluginImplementation
public class CryptoExchangePoloniexPlugin
extends Exchange {
    private JSONArray availableSymbols = null;

    public String getName() {
        return "Poloniex";
    }

    public JSONArray getSymbols() throws Exception {
        if (this.availableSymbols != null) {
            return this.availableSymbols;
        }
        String response = new String(HttpApacheManager.getInstance().getData("https://api.poloniex.com/markets"));
        JSONArray array = new JSONArray(response);
        JSONArray symbols = new JSONArray();
        for (int i = 0; i < array.length(); ++i) {
            JSONObject symbolInfo = array.getJSONObject(i);
            String pair = symbolInfo.getString("symbol");
            symbols.put((Object)pair);
        }
        this.availableSymbols = symbols;
        return this.availableSymbols;
    }

    public IExchange clone() {
        return new CryptoExchangePoloniexPlugin();
    }

    public void download() throws Exception {
        long startTime;
        long timeframeMs = TimeframeManager.getMillis((String)this.dataInfo.timeframe);
        String timeframe = this.convertTimeframe(this.dataInfo.timeframe);
        long l = startTime = this.importInfo.dateFrom > 0L ? this.importInfo.dateFrom : 0L;
        if (startTime == 0L) {
            startTime = this.getMinimalDate(this.dataInfo.uSymbol);
        }
        startTime = this.dataMerger.checkDate(startTime);
        int limit = 500;
        while (startTime <= this.importInfo.dateTo) {
            long endTime = this.getEndOfTime(startTime, limit - 1, this.dataInfo.timeframe);
            String link = "https://api.poloniex.com/markets/" + this.dataInfo.uSymbol + "/candles?limit=" + limit + "&interval=" + timeframe + "&startTime=" + startTime + "&endTime=" + endTime;
            long startPerformed = this.dataMerger.getPerformedDays();
            long startCycleTime = System.currentTimeMillis();
            String response = this.doDownload(link);
            long downloadedDuration = System.currentTimeMillis() - startCycleTime;
            JSONArray array = new JSONArray(response);
            this.dataMerger.register(0, startTime);
            this.dataMerger.reset(1);
            Long lastDate = null;
            for (int i = 0; i < array.length(); ++i) {
                VersatileData data = this.parseData(array.getJSONArray(i));
                if (data.time > this.importInfo.dateTo) break;
                this.dataMerger.storeToQueue(0, data);
                lastDate = data.time;
            }
            this.dataMerger.tryToSaveQueue(startTime);
            startTime = lastDate == null ? this.importInfo.dateTo + timeframeMs : lastDate + timeframeMs;
            this.checkPaused();
            if (this.canceled && !this.stopping) {
                this.importInfo.dateTo = SQTime.correctDayEnd((long)startTime);
                this.stopping = true;
            }
            this.evaluateSpeed(startCycleTime, startPerformed, response.getBytes().length, downloadedDuration);
            Thread.sleep(250L);
            if (this.dataMerger.getReader() == null) continue;
            this.dataMerger.readTill(startTime, false);
        }
    }

    private long getEndOfTime(long startTime, int limit, String tf) throws Exception {
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
                return SQTime.addMinutes((long)startTime, (int)(count * limit));
            }
            case "H": {
                return SQTime.addHours((long)startTime, (int)(count * limit));
            }
            case "D": {
                return SQTime.addDays((long)startTime, (int)(count * limit));
            }
        }
        throw new Exception(L.t((String)"Invalid timeframe format. Prefix '%s' not recognized.", (Object[])new Object[]{prefix}));
    }

    private long getMinimalDate(String symbol) {
        String response;
        try {
            response = new String(HttpApacheManager.getInstance().getData("https://api.poloniex.com/markets/" + symbol));
        }
        catch (Exception e) {
            Log.error("Error while downloading symbol info", (Throwable)e);
            throw new RuntimeException("Error while downloading symbol info");
        }
        JSONArray items = new JSONArray(response);
        JSONObject item = items.getJSONObject(0);
        return item.getLong("visibleStartTime");
    }

    private VersatileData parseData(JSONArray arr) {
        VersatileData data = new VersatileData();
        data.time = arr.getLong(12);
        data.open = arr.getDouble(2);
        data.high = arr.getDouble(1);
        data.low = arr.getDouble(0);
        data.close = arr.getDouble(3);
        data.volume = arr.getDouble(4);
        return data;
    }

    public JSONArray availableTimeframes() {
        return new JSONArray().put((Object)"M5").put((Object)"M15").put((Object)"M30").put((Object)"H2").put((Object)"H4").put((Object)"D1");
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
                return "MINUTE_" + count;
            }
            case "H": {
                return "HOUR_" + count;
            }
            case "D": {
                return "DAY_" + count;
            }
        }
        throw new Exception(L.t((String)"Invalid timeframe format. Prefix '%s' not recognized.", (Object[])new Object[]{prefix}));
    }

    public boolean checkSymbolExists(String symbol) {
        try {
            String response = new String(HttpApacheManager.getInstance().getData("https://api.poloniex.com/markets/" + symbol));
            new JSONArray(response);
        }
        catch (Exception e) {
            return false;
        }
        return true;
    }

    public SymbolInfo getSymbolInfo(String symbol) {
        try {
            String response = new String(HttpApacheManager.getInstance().getData("https://api.poloniex.com/markets/" + symbol));
            JSONArray jsonArray = new JSONArray(response);
            JSONObject jsonSymbolInfo = jsonArray.getJSONObject(0).getJSONObject("symbolTradeLimit");
            SymbolInfo symbolInfo = new SymbolInfo();
            int priceScale = jsonSymbolInfo.getInt("priceScale");
            double value = BigDecimal.ONE.movePointLeft(priceScale).doubleValue();
            symbolInfo.setTickSize(value);
            symbolInfo.setTickStep(value);
            return symbolInfo;
        }
        catch (Exception e) {
            throw new RuntimeException("Error while fetching symbol info", e);
        }
    }
}

