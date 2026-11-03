/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.memory.CpuInfo
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.tradinglib.ResultsGroup
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades;

import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.memory.CpuInfo;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationInterruptException;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationResultsSender;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingResult;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTrade;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.overlappingTrades.OverlappingTradesTask;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class OverlappingTradesComputer {
    private static final Logger Log = LoggerFactory.getLogger(OverlappingTradesComputer.class);
    private HashMap<String, OverlappingResult> results = new HashMap();
    public boolean stopped;

    public JSONObject compute(ResultsGroup strategy, PortfolioCorrelationResultsSender sender) throws Exception {
        this.stopped = false;
        int numberOfProcessors = CpuInfo.getAvailableProcessors();
        ExecutorService executor = Executors.newFixedThreadPool(numberOfProcessors);
        try {
            String key;
            this.results.clear();
            ArrayList<Future<OverlappingResult>> futureList = new ArrayList<Future<OverlappingResult>>();
            List symbolList = strategy.getResultKeys();
            for (String symbol1 : symbolList) {
                if (this.stopped) {
                    throw new PortfolioCorrelationInterruptException();
                }
                if (symbol1.equals("Portfolio") || symbol1.startsWith("WF:") || symbol1.startsWith("CrossCheck_")) continue;
                for (String symbol2 : symbolList) {
                    if (this.stopped) {
                        throw new PortfolioCorrelationInterruptException();
                    }
                    if (symbol2.equals("Portfolio") || symbol2.startsWith("WF:") || symbol2.startsWith("CrossCheck_") || symbol1.equals(symbol2) || this.results.containsKey(key = this.key(symbol1, symbol2))) continue;
                    this.results.put(key, null);
                    futureList.add(executor.submit(new OverlappingTradesTask(symbol1, symbol2, strategy)));
                }
            }
            int done = 0;
            for (Future future : futureList) {
                if (this.stopped) {
                    throw new PortfolioCorrelationInterruptException();
                }
                OverlappingResult result = (OverlappingResult)future.get();
                double pct = 50.0 + (double)(++done) / (double)this.results.size() * 100.0 / 2.0;
                sender.progress((int)pct);
                key = this.key(result.symbol1, result.symbol2);
                this.results.put(key, result);
            }
            return this.printResults(symbolList);
        }
        catch (PortfolioCorrelationInterruptException e) {
            executor.shutdownNow();
            throw e;
        }
        catch (Exception e) {
            Log.error("Error while computing overlapping trades.", (Throwable)e);
            throw e;
        }
    }

    private JSONObject printResults(List<String> symbolList) {
        JSONObject data = new JSONObject();
        String overlappingKey = null;
        JSONArray columns = new JSONArray();
        columns.put((Object)"");
        JSONArray rows = new JSONArray();
        for (int i = 0; i < symbolList.size(); ++i) {
            String symbol1 = symbolList.get(i);
            if (symbol1.equals("Portfolio") || symbol1.startsWith("WF:") || symbol1.startsWith("CrossCheck_")) continue;
            columns.put((Object)symbol1);
            JSONArray rowData = new JSONArray();
            rowData.put((Object)symbol1);
            for (String symbol2 : symbolList) {
                if (symbol2.equals("Portfolio") || symbol2.startsWith("WF:") || symbol2.startsWith("CrossCheck_")) continue;
                if (symbol1.equals(symbol2)) {
                    rowData.put((Object)"");
                    continue;
                }
                overlappingKey = this.key(symbol1, symbol2);
                OverlappingResult result = this.results.get(overlappingKey);
                rowData.put(result.count);
            }
            JSONObject row = new JSONObject();
            row.put("id", (Object)("r" + i));
            row.put("data", (Object)rowData);
            rows.put((Object)row);
        }
        data.put("columns", (Object)columns);
        data.put("rows", (Object)rows);
        return data;
    }

    private String key(String symbol1, String symbol2) {
        return symbol1.compareTo(symbol2) > 0 ? symbol1 + "-" + symbol2 : symbol2 + "-" + symbol1;
    }

    public String list(String symbol1, String symbol2, int posStart, int count) {
        JsonCreator json = new JsonCreator();
        json.beginObject();
        json.put("rows");
        String key = this.key(symbol1, symbol2);
        OverlappingResult result = this.results.get(key);
        json.beginArray();
        for (int i = posStart; i < result.data.size(); ++i) {
            OverlappingTrade trade = result.data.get(i);
            if (i >= posStart + count) break;
            if (i != posStart) {
                json.separator();
            }
            json.beginObject();
            json.put("data");
            json.beginArray();
            json.setValue((Object)(i + 1), true);
            json.setValue((Object)SQTime.toString((long)trade.from1), true);
            json.setValue((Object)SQTime.toString((long)trade.to1), true);
            json.setValue((Object)SQTime.toString((long)trade.from2), true);
            json.setValue((Object)SQTime.toString((long)trade.to2), true);
            json.setValue((Object)trade.time, false);
            json.endArray(true);
            json.put("id", (Object)("r" + i), false);
            json.endObject(false);
        }
        json.endArray(true);
        json.put("pos", (Object)posStart, true);
        json.put("total_count", (Object)result.data.size(), true);
        json.put("success", (Object)"ok", false);
        json.endObject(false);
        return json.toJson();
    }

    public void stop() {
        this.stopped = true;
    }

    public void clear() {
        this.results.clear();
    }
}

