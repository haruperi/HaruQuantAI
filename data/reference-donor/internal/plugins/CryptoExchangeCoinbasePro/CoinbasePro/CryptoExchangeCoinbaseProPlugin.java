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
package com.strategyquant.plugin.CryptoExchange.impl.CoinbasePro;

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
import java.text.SimpleDateFormat;
import java.util.Date;
import net.xeoh.plugins.base.annotations.PluginImplementation;
import net.xeoh.plugins.base.annotations.meta.Author;
import org.json.JSONArray;
import org.json.JSONObject;

@Author(name="Tomas Takacs")
@Name(name="Coinbase")
@Category(name="Server Extension")
@License(text="")
@ShortDesc(text="Server API for managing Coinbase Pro data")
@PluginImplementation
public class CryptoExchangeCoinbaseProPlugin
extends Exchange {
    private JSONArray availableSymbols = null;

    public String getName() {
        return "Coinbase Pro";
    }

    public JSONArray getSymbols() throws Exception {
        if (this.availableSymbols != null) {
            return this.availableSymbols;
        }
        String response = new String(HttpApacheManager.getInstance().getData("https://api.exchange.coinbase.com/products"));
        JSONArray symbols = new JSONArray();
        JSONArray array = new JSONArray(response);
        for (int i = 0; i < array.length(); ++i) {
            JSONObject obj = array.getJSONObject(i);
            boolean disabled = obj.getBoolean("trading_disabled");
            if (disabled) continue;
            symbols.put((Object)obj.getString("id"));
        }
        this.availableSymbols = symbols;
        return this.availableSymbols;
    }

    public IExchange clone() {
        return new CryptoExchangeCoinbaseProPlugin();
    }

    private long getEarliestTime() throws Exception {
        long earliestDate = 0L;
        long startTime = 1000L;
        long timeframeMs = TimeframeManager.getMillis((String)"D290");
        while (earliestDate == 0L) {
            long[] times = this.getFutureEarliestAndLargestTime(startTime);
            if (times[0] > 0L) {
                earliestDate = times[0];
            }
            startTime += timeframeMs;
            Thread.sleep(333L);
        }
        return earliestDate;
    }

    private long[] getFutureEarliestAndLargestTime(long startTime) throws Exception {
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        long timeframeMs = TimeframeManager.getMillis((String)"D290");
        long earliestDataTime = 0L;
        long largestDataTime = 0L;
        Date date = new Date();
        date.setTime(startTime);
        String link = "https://api.exchange.coinbase.com/products/" + this.dataInfo.uSymbol + "/candles?granularity=86400&start=" + sdf.format(date);
        date.setTime(startTime + timeframeMs);
        link = link + "&end=" + sdf.format(date);
        String response = this.doDownload(link);
        JSONArray array = new JSONArray(response);
        if (array.length() > 0) {
            VersatileData earliestData = this.parseData(array.getJSONArray(array.length() - 1));
            VersatileData latestData = this.parseData(array.getJSONArray(0));
            earliestDataTime = earliestData.time;
            largestDataTime = latestData.time;
        }
        long[] times = new long[]{earliestDataTime, largestDataTime};
        return times;
    }

    public void download() throws Exception {
        String response = null;
        long futureLargestDataTime = 0L;
        long futureEarliestDataTime = 0L;
        long timeframeMs = TimeframeManager.getMillis((String)this.dataInfo.timeframe);
        String timeframe = this.convertTimeframe(this.dataInfo.timeframe);
        long startTime = this.importInfo.dateFrom > 0L ? this.importInfo.dateFrom : this.getEarliestTime();
        startTime = this.dataMerger.checkDate(startTime);
        Date date = new Date();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'");
        long records = 0L;
        String origProtocols = System.getProperty("https.protocols");
        System.setProperty("https.protocols", "TLSv1.2");
        while (startTime <= this.importInfo.dateTo) {
            date.setTime(startTime);
            String link = "https://api.exchange.coinbase.com/products/" + this.dataInfo.uSymbol + "/candles?granularity=" + timeframe + "&start=" + sdf.format(date);
            long startPerformed = this.dataMerger.getPerformedDays();
            long startCycleTime = System.currentTimeMillis();
            this.dataMerger.register(0, startTime / 1000L);
            this.dataMerger.reset(1);
            date.setTime(startTime + 299L * timeframeMs);
            link = link + "&end=" + sdf.format(date);
            try {
                response = this.doDownload(link);
            }
            catch (Exception e) {
                if (e.getMessage().contains("429")) {
                    throw new Exception(L.t((String)"Rate limit exceeded.", (Object[])new Object[0]));
                }
                throw e;
            }
            JSONArray array = new JSONArray(response);
            if (array.length() == 0) {
                Thread.sleep(333L);
                long[] times = this.getFutureEarliestAndLargestTime(startTime + 299L * timeframeMs);
                futureEarliestDataTime = times[0];
                futureLargestDataTime = times[1];
                if (startTime > futureLargestDataTime) break;
                startTime = futureEarliestDataTime - 1000L;
            } else {
                long downloadedDuration = System.currentTimeMillis() - startCycleTime;
                for (int i = array.length() - 1; i >= 0; --i) {
                    VersatileData data = this.parseData(array.getJSONArray(i));
                    if (records == 0L && data.time > this.importInfo.dateTo) {
                        Log.warn("Date from for this cryptocurrency is not correct, this exchange doesn't have history this long. Please enter the correct date from.");
                        continue;
                    }
                    if (data.time > this.importInfo.dateTo) break;
                    this.dataMerger.storeToQueue(0, data);
                }
                this.dataMerger.tryToSaveQueue(startTime);
                startTime = array.getJSONArray(0).getLong(0) * 1000L;
                startTime += timeframeMs;
                ++records;
                this.evaluateSpeed(startCycleTime, startPerformed, response.getBytes().length, downloadedDuration);
                if (this.dataMerger.getReader() != null) {
                    this.dataMerger.readTill(startTime, false);
                }
            }
            if (this.canceled && !this.stopping) {
                this.importInfo.dateTo = SQTime.correctDayEnd((long)startTime);
                this.stopping = true;
            }
            this.checkPaused();
            Thread.sleep(333L);
        }
        if (origProtocols == null) {
            System.clearProperty("https.protocols");
        } else {
            System.setProperty("https.protocols", origProtocols);
        }
    }

    private VersatileData parseData(JSONArray jsonArray) {
        VersatileData data = new VersatileData();
        data.time = jsonArray.getLong(0) * 1000L;
        data.low = jsonArray.getDouble(1);
        data.high = jsonArray.getDouble(2);
        data.open = jsonArray.getDouble(3);
        data.close = jsonArray.getDouble(4);
        data.volume = jsonArray.getDouble(5);
        return data;
    }

    public JSONArray availableTimeframes() {
        return new JSONArray().put((Object)"M1").put((Object)"M5").put((Object)"M15").put((Object)"H1").put((Object)"H6").put((Object)"D1");
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
                return String.valueOf(count * 60);
            }
            case "H": {
                return String.valueOf(count * 3600);
            }
            case "D": {
                return String.valueOf(count * 86400);
            }
        }
        throw new Exception(L.t((String)"Invalid timeframe format. Prefix '%s' not recognized.", (Object[])new Object[]{prefix}));
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public boolean checkSymbolExists(String symbol) {
        String origProtocols = System.getProperty("https.protocols");
        try {
            System.setProperty("https.protocols", "TLSv1.2");
            String response = new String(HttpApacheManager.getInstance().getData("https://api.exchange.coinbase.com/products/" + symbol + "/ticker"));
            JSONObject object = new JSONObject(response);
            object.getString("price");
        }
        catch (Exception e) {
            boolean bl = false;
            return bl;
        }
        finally {
            if (origProtocols == null) {
                System.clearProperty("https.protocols");
            } else {
                System.setProperty("https.protocols", origProtocols);
            }
        }
        return true;
    }

    public SymbolInfo getSymbolInfo(String symbol) {
        String response;
        String link = "https://api.exchange.coinbase.com/products/" + symbol;
        try {
            response = this.doDownload(link);
        }
        catch (Exception e) {
            throw new RuntimeException("Error while downloading symbol info", e);
        }
        JSONObject jsonObj = new JSONObject(response);
        String quoteStr = jsonObj.getString("quote_increment");
        SymbolInfo symbolInfo = new SymbolInfo();
        symbolInfo.setTickSize(Double.valueOf(quoteStr).doubleValue());
        symbolInfo.setTickStep(Double.valueOf(quoteStr).doubleValue());
        return symbolInfo;
    }
}

