/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SQStats
 *  com.strategyquant.tradinglib.databank.RecordNotFoundException
 *  com.strategyquant.tradinglib.results.IResultsGroupProvider
 *  com.strategyquant.tradinglib.strategyConfig.StrategyConfig
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.SPOverview;

import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SQStats;
import com.strategyquant.tradinglib.databank.RecordNotFoundException;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.strategyConfig.StrategyConfig;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import it.unimi.dsi.fastutil.objects.Object2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SPOverviewServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SPOverviewServlet.class);
    private static final String LOCK_SPOVERVIEWSERVLET = "SPOverviewServlet";
    private static IResultsGroupProvider rgProvider;
    private StrategyConfig strategyConfig = new StrategyConfig();

    public SPOverviewServlet(IResultsGroupProvider provider) {
        rgProvider = provider;
    }

    protected String execute(String command, Map<String, String[]> args, String method) throws Exception {
        switch (command) {
            case "print": {
                return this.onPrint(args);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private String onPrint(Map<String, String[]> parameterMap) throws Exception {
        int i;
        SPStock stock;
        String symbol;
        JSONObject response = new JSONObject();
        boolean showAll = Boolean.valueOf(this.tryGetParam(parameterMap, "showAll")[0]);
        OrdersList orders = null;
        ResultsGroup resultsGroup = null;
        try {
            resultsGroup = rgProvider.get(parameterMap, LOCK_SPOVERVIEWSERVLET);
            orders = resultsGroup.orders();
        }
        catch (RecordNotFoundException e) {
            Log.info("onPrint: " + e.getMessage());
            String string = SPOverviewServlet.apiErrorJSONNoLog(null, (Exception)((Object)e));
            return string;
        }
        finally {
            if (resultsGroup != null) {
                resultsGroup.releaseLock(LOCK_SPOVERVIEWSERVLET);
            }
        }
        Object2ObjectOpenHashMap stocks = new Object2ObjectOpenHashMap();
        double totalProfit = 0.0;
        double totalLoss = 0.0;
        double totalVolume = 0.0;
        for (int i2 = 0; i2 < orders.size(); ++i2) {
            Order order = orders.get(i2);
            if (!order.isFilledOrder() || !order.isRealOrder()) continue;
            symbol = order.Symbol;
            if (!stocks.containsKey((Object)symbol)) {
                stocks.put((Object)symbol, (Object)new SPStock(symbol));
            }
            stock = (SPStock)stocks.get((Object)symbol);
            stock.pl += (double)order.PL;
            stock.volume += (double)order.Size;
            ++stock.trades;
            if (order.PL > 0.0f) {
                totalProfit += (double)order.PL;
            } else {
                totalLoss += (double)order.PL;
            }
            totalVolume += (double)order.Size;
        }
        JSONObject treeMap = new JSONObject();
        JSONArray treeMapData = new JSONArray();
        treeMap.put("data", (Object)treeMapData);
        JSONObject listAll = new JSONObject();
        JSONArray rowsAll = new JSONArray();
        listAll.put("rows", (Object)rowsAll);
        ArrayList keys = new ArrayList(stocks.keySet());
        Collections.sort(keys);
        double pctVolume = 0.0;
        double pctPL = 0.0;
        double min = 0.0;
        double max = 0.0;
        ArrayList<SPStock> stockList = new ArrayList<SPStock>();
        for (i = 0; i < keys.size(); ++i) {
            symbol = (String)keys.get(i);
            stock = (SPStock)stocks.get((Object)symbol);
            stockList.add(stock);
        }
        stockList.sort(new StockComparatorByVolume());
        for (i = 0; i < stockList.size(); ++i) {
            stock = (SPStock)stockList.get(i);
            rowsAll.put((Object)new JSONObject().put("id", (Object)("r" + i)).put("data", (Object)new JSONArray().put(i + 1).put((Object)stock.symbol).put(SQUtils.round2((double)stock.pl)).put(stock.volume).put(stock.trades)));
            pctVolume = stock.volume / totalVolume * 100.0;
            if (stock.pl < 0.0) {
                pctVolume *= -1.0;
                pctPL = stock.pl / totalLoss * 100.0 * -1.0;
                if (stock.pl < min) {
                    min = stock.pl;
                }
            } else {
                pctPL = stock.pl / totalProfit * 100.0;
                if (stock.pl > max) {
                    max = stock.pl;
                }
            }
            treeMapData.put((Object)new JSONObject().put("x", (Object)stock.symbol).put("y", SQUtils.round2((double)pctVolume)).put("v", SQUtils.round2((double)pctPL)).put("pl", SQUtils.round2((double)stock.pl)));
            if (!showAll && rowsAll.length() == 100) break;
        }
        treeMap.put("min", SQUtils.round2((double)min));
        treeMap.put("max", SQUtils.round2((double)max));
        JSONArray top10Profit = new JSONArray();
        stockList.sort(new StockComparatorByPL());
        this.copyData(stockList, top10Profit, totalProfit, false, true);
        JSONArray top10Loss = new JSONArray();
        Collections.reverse(stockList);
        this.copyData(stockList, top10Loss, totalLoss, false, false);
        JSONArray top10Volume = new JSONArray();
        stockList.sort(new StockComparatorByVolume());
        this.copyData(stockList, top10Volume, totalVolume, true, false);
        response.put("stats", (Object)this.getStats(resultsGroup));
        response.put("treeMap", (Object)treeMap);
        response.put("top10Profit", (Object)top10Profit);
        response.put("top10Loss", (Object)top10Loss);
        response.put("top10Volume", (Object)top10Volume);
        response.put("listAll", (Object)listAll);
        response.put("success", (Object)"ok");
        return response.toString();
    }

    private JSONObject getStats(ResultsGroup resultsGroup) throws Exception {
        JSONObject stats = new JSONObject();
        SQStats statsRg = resultsGroup.portfolio().stats((byte)0, (byte)10, (byte)127);
        stats.put("NetProfit", (Object)SQUtils.d2((double)statsRg.getDouble("NetProfit")));
        stats.put("AvgProfitPerYear", (Object)SQUtils.d2((double)statsRg.getDouble("AvgProfitPerYear")));
        stats.put("CAGR", (Object)SQUtils.d2((double)statsRg.getDouble("CAGR")));
        stats.put("NumberOfTrades", statsRg.getInt("NumberOfTrades"));
        stats.put("SharpeRatio", statsRg.getInt("SharpeRatio"));
        stats.put("ProfitFactor", (Object)SQUtils.d2((double)statsRg.getDouble("ProfitFactor")));
        stats.put("ReturnDDRatio", (Object)SQUtils.d2((double)statsRg.getDouble("ReturnDDRatio")));
        stats.put("AvgTrade", (Object)SQUtils.d2((double)statsRg.getDouble("AvgTrade")));
        stats.put("Drawdown", (Object)SQUtils.d2((double)statsRg.getDouble("Drawdown")));
        stats.put("DrawdownPct", (Object)SQUtils.d2((double)statsRg.getDouble("DrawdownPct")));
        stats.put("Exposure", (Object)SQUtils.d2((double)statsRg.getDouble("Exposure")));
        stats.put("AnnualPctReturnDDRatio", (Object)SQUtils.d2((double)statsRg.getDouble("AnnualPctReturnDDRatio")));
        stats.put("AvgProfitPerMonth", (Object)SQUtils.d2((double)statsRg.getDouble("AvgProfitPerMonth")));
        return stats;
    }

    private void copyData(List<SPStock> stockList, JSONArray jsonList, double total, boolean volume, boolean onlyPositivePL) {
        for (int i = 0; i < Math.min(10, stockList.size()); ++i) {
            double pct;
            SPStock stock = stockList.get(i);
            if (volume) {
                pct = stock.volume / total * 100.0;
            } else {
                if (onlyPositivePL && stock.pl <= 0.0 || !onlyPositivePL && stock.pl >= 0.0) {
                    jsonList.put((Object)new JSONObject().put("x", (Object)"").put("y", 0));
                    continue;
                }
                pct = stock.pl / total * 100.0;
            }
            jsonList.put((Object)new JSONObject().put("x", (Object)stock.symbol).put("y", SQUtils.round2((double)pct)));
        }
    }

    private class SPStock {
        public String symbol;
        public double pl;
        public double volume;
        public long trades;

        public SPStock(String symbol) {
            this.symbol = symbol;
            this.pl = 0.0;
            this.volume = 0.0;
            this.trades = 0L;
        }
    }

    public class StockComparatorByVolume
    implements Comparator<SPStock> {
        @Override
        public int compare(SPStock order1, SPStock order2) {
            if (order1.volume > order2.volume) {
                return -1;
            }
            if (order1.volume < order2.volume) {
                return 1;
            }
            return 0;
        }
    }

    public class StockComparatorByPL
    implements Comparator<SPStock> {
        @Override
        public int compare(SPStock order1, SPStock order2) {
            if (order1.pl > order2.pl) {
                return -1;
            }
            if (order1.pl < order2.pl) {
                return 1;
            }
            return 0;
        }
    }
}

