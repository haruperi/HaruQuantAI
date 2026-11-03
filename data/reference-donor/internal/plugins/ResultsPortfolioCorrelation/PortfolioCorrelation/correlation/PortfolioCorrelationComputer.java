/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TimePeriod
 *  com.strategyquant.lib.TimePeriods
 *  com.strategyquant.lib.memory.CpuInfo
 *  com.strategyquant.lib.utils.JsonCreator
 *  com.strategyquant.tradinglib.CorrelationLib
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.CustomCellFormat
 *  com.strategyquant.tradinglib.Order
 *  com.strategyquant.tradinglib.OrdersList
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.correlation.CorrelationPeriodTypes
 *  com.strategyquant.tradinglib.correlation.CorrelationPeriods
 *  it.unimi.dsi.fastutil.longs.Long2ObjectMap$Entry
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TimePeriod;
import com.strategyquant.lib.TimePeriods;
import com.strategyquant.lib.memory.CpuInfo;
import com.strategyquant.lib.utils.JsonCreator;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationInterruptException;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.PortfolioCorrelationResultsSender;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation.CorrelationComputerTask;
import com.strategyquant.plugin.Results.impl.PortfolioCorrelation.correlation.CorrelationResult;
import com.strategyquant.tradinglib.CorrelationLib;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.CustomCellFormat;
import com.strategyquant.tradinglib.Order;
import com.strategyquant.tradinglib.OrdersList;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.correlation.CorrelationPeriodTypes;
import com.strategyquant.tradinglib.correlation.CorrelationPeriods;
import it.unimi.dsi.fastutil.longs.Long2ObjectMap;
import java.io.PrintWriter;
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

public class PortfolioCorrelationComputer {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioCorrelationComputer.class);
    private HashMap<String, CorrelationResult> results = new HashMap();
    private boolean allowNegativeCorrelation;
    boolean addEmptyPeriods;
    private CustomCellFormat cellFormat = new CustomCellFormat();
    private CorrelationType type;
    private int period;
    private List<String> symbolList;
    private CorrelationPeriods periods;
    public boolean stopped;

    public JSONObject compute(ResultsGroup strategy, int period, CorrelationType type, boolean allowNegativeCorrelation, boolean addEmptyPeriods, PortfolioCorrelationResultsSender sender) throws Exception {
        this.allowNegativeCorrelation = allowNegativeCorrelation;
        this.addEmptyPeriods = addEmptyPeriods;
        this.period = period;
        this.type = type;
        this.stopped = false;
        int numberOfProcessors = CpuInfo.getAvailableProcessors();
        ExecutorService executor = Executors.newFixedThreadPool(numberOfProcessors);
        try {
            String key;
            this.results.clear();
            this.periods = this.precomputePeriods(strategy);
            ArrayList<Future<CorrelationResult>> futureList = new ArrayList<Future<CorrelationResult>>();
            this.symbolList = strategy.getResultKeys();
            for (String symbol1 : this.symbolList) {
                if (this.stopped) {
                    throw new PortfolioCorrelationInterruptException();
                }
                if (symbol1.equals("Portfolio") || symbol1.startsWith("WF:") || symbol1.startsWith("CrossCheck_")) continue;
                for (String symbol2 : this.symbolList) {
                    if (this.stopped) {
                        throw new PortfolioCorrelationInterruptException();
                    }
                    if (symbol2.equals("Portfolio") || symbol2.startsWith("WF:") || symbol2.startsWith("CrossCheck_") || symbol1.equals(symbol2) || this.results.containsKey(key = this.key(symbol1, symbol2))) continue;
                    this.results.put(key, null);
                    futureList.add(executor.submit(new CorrelationComputerTask(strategy, symbol1, symbol2, period, type, allowNegativeCorrelation, addEmptyPeriods, this.periods)));
                }
            }
            int done = 0;
            for (Future future : futureList) {
                if (this.stopped) {
                    throw new PortfolioCorrelationInterruptException();
                }
                CorrelationResult result = (CorrelationResult)future.get();
                double pct = (double)(++done) / (double)this.results.size() * 100.0 / 2.0;
                if (result == null) continue;
                sender.progress((int)pct);
                key = this.key(result.symbol1, result.symbol2);
                this.results.put(key, result);
            }
            return this.printResults(period, type);
        }
        catch (PortfolioCorrelationInterruptException e) {
            executor.shutdownNow();
            throw e;
        }
        catch (Exception e) {
            Log.error("Error while computing portfolio correlation.", (Throwable)e);
            throw e;
        }
    }

    private CorrelationPeriods precomputePeriods(ResultsGroup rg) throws Exception {
        CorrelationPeriods correlationPeriods = new CorrelationPeriods();
        TimePeriod range = CorrelationLib.getPeriod((OrdersList)rg.orders());
        TimePeriods periods = CorrelationLib.generatePeriods((int)this.period, (long)range.from, (long)range.to);
        List symbolList = rg.getResultKeys();
        for (String symbol : symbolList) {
            if (this.stopped) {
                throw new PortfolioCorrelationInterruptException();
            }
            if (symbol.equals("Portfolio") || symbol.startsWith("WF:") || symbol.startsWith("CrossCheck_")) continue;
            OrdersList orders = this.createOrdersFromStrategy(rg, symbol);
            TimePeriods periodsClone = periods.clone();
            this.type.computePeriods(orders, this.period, periodsClone);
            correlationPeriods.put((Object)symbol, (Object)periodsClone);
        }
        return correlationPeriods;
    }

    private OrdersList createOrdersFromStrategy(ResultsGroup rg, String symbol) throws Exception {
        OrdersList orders = new OrdersList("orders");
        OrdersList allOrders = rg.orders();
        for (int i = 0; i < allOrders.size(); ++i) {
            Order o = allOrders.get(i);
            if (!o.isRealOrder() || !o.SetupName.equals(symbol)) continue;
            orders.add(o);
        }
        return orders;
    }

    private JSONObject printResults(int period, CorrelationType type) throws Exception {
        this.cellFormat.reset();
        JSONObject data = new JSONObject();
        String correlationKey = null;
        JSONArray columns = new JSONArray();
        columns.put((Object)"");
        JSONArray rows = new JSONArray();
        for (int i = 0; i < this.symbolList.size(); ++i) {
            String symbol1 = this.symbolList.get(i);
            if (symbol1.equals("Portfolio") || symbol1.startsWith("WF:") || symbol1.startsWith("CrossCheck_")) continue;
            columns.put((Object)symbol1);
            JSONArray rowData = new JSONArray();
            rowData.put((Object)symbol1);
            for (String symbol2 : this.symbolList) {
                if (symbol2.equals("Portfolio") || symbol2.startsWith("WF:") || symbol2.startsWith("CrossCheck_")) continue;
                if (symbol1.equals(symbol2)) {
                    rowData.put((Object)"");
                    continue;
                }
                correlationKey = this.key(symbol1, symbol2);
                CorrelationResult result = this.results.get(correlationKey);
                if (result == null) continue;
                this.cellFormat.customStyle = "background-color: " + this.getColor(result.value) + ";";
                this.cellFormat.customStyle = this.cellFormat.customStyle + "color: " + this.getTextColor(result.value) + ";";
                rowData.put((Object)this.cellFormat.getHtmlContent((Object)SQUtils.d2((double)result.value)));
            }
            JSONObject row = new JSONObject();
            row.put("id", (Object)("r" + i));
            row.put("data", (Object)rowData);
            rows.put((Object)row);
        }
        data.put("type", (Object)type.getName());
        data.put("period", (Object)CorrelationPeriodTypes.toString((int)period));
        data.put("columns", (Object)columns);
        data.put("dataType", (Object)(type.getDataType() == 5 ? "Profit/Loss" : "# of trades"));
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
        this.cellFormat.reset();
        json.beginArray();
        TimePeriods periodsSymbol1 = (TimePeriods)this.periods.get((Object)symbol1);
        TimePeriods periodsSymbol2 = (TimePeriods)this.periods.get((Object)symbol2);
        if (!this.addEmptyPeriods) {
            TimePeriods filtered1 = new TimePeriods();
            TimePeriods filtered2 = new TimePeriods();
            this.filterEmptyPeriods(periodsSymbol1, periodsSymbol2, filtered1, filtered2);
            periodsSymbol1 = filtered1;
            periodsSymbol2 = filtered2;
        }
        int i = -1;
        for (Long2ObjectMap.Entry item : periodsSymbol1.long2ObjectEntrySet()) {
            if (++i < posStart) continue;
            if (i >= posStart + count) break;
            if (i != posStart) {
                json.separator();
            }
            long time = item.getLongKey();
            double value1 = ((TimePeriod)periodsSymbol1.get((long)time)).value;
            double value2 = ((TimePeriod)periodsSymbol2.get((long)time)).value;
            String period = ((TimePeriod)periodsSymbol1.get((long)time)).name;
            json.beginObject();
            json.put("data");
            json.beginArray();
            json.setValue((Object)(i + 1), true);
            json.setValue((Object)period, true);
            this.cellFormat.customStyle = "color: " + this.getColor2(value1) + ";";
            json.setValue((Object)this.cellFormat.getHtmlContent(this.type.getDataType() == 5 ? SQUtils.d2((double)value1) : Integer.valueOf((int)value1)), true);
            this.cellFormat.customStyle = "color: " + this.getColor2(value2) + ";";
            json.setValue((Object)this.cellFormat.getHtmlContent(this.type.getDataType() == 5 ? SQUtils.d2((double)value2) : Integer.valueOf((int)value2)), false);
            json.endArray(true);
            json.put("id", (Object)("r" + i), false);
            json.endObject(false);
        }
        json.endArray(true);
        json.put("pos", (Object)posStart, true);
        json.put("total_count", (Object)periodsSymbol1.size(), true);
        json.put("success", (Object)"ok", false);
        json.endObject(false);
        return json.toJson();
    }

    private void filterEmptyPeriods(TimePeriods periodsSymbol1, TimePeriods periodsSymbol2, TimePeriods filtered1, TimePeriods filtered2) {
        for (Long2ObjectMap.Entry item : periodsSymbol1.long2ObjectEntrySet()) {
            long time = item.getLongKey();
            if (!this.addEmptyPeriods && ((TimePeriod)periodsSymbol1.get((long)time)).value == 0.0 && ((TimePeriod)periodsSymbol2.get((long)time)).value == 0.0) continue;
            filtered1.put(item.getLongKey(), (Object)((TimePeriod)periodsSymbol1.get(time)));
            filtered2.put(item.getLongKey(), (Object)((TimePeriod)periodsSymbol2.get(time)));
        }
    }

    public void saveToCsv(String path) throws Exception {
        try {
            int i;
            if (!path.toLowerCase().endsWith(".csv")) {
                path = path + ".csv";
            }
            String correlationKey = null;
            PrintWriter writer = new PrintWriter(path);
            writer.print("\"\";");
            for (i = 0; i < this.symbolList.size(); ++i) {
                String symbol = this.symbolList.get(i);
                if (symbol.equals("Portfolio") || symbol.startsWith("WF:") || symbol.startsWith("CrossCheck_")) continue;
                writer.print("\"" + symbol + "\"");
                if (i == this.symbolList.size() - 1) continue;
                writer.print(";");
            }
            writer.println();
            for (i = 0; i < this.symbolList.size(); ++i) {
                String symbol1 = this.symbolList.get(i);
                if (symbol1.equals("Portfolio") || symbol1.startsWith("WF:") || symbol1.startsWith("CrossCheck_")) continue;
                writer.print("\"" + symbol1 + "\";");
                for (int j = 0; j < this.symbolList.size(); ++j) {
                    String symbol2 = this.symbolList.get(j);
                    if (symbol2.equals("Portfolio") || symbol2.startsWith("WF:") || symbol2.startsWith("CrossCheck_")) continue;
                    if (symbol1.equals(symbol2)) {
                        writer.print("\"\";");
                        continue;
                    }
                    correlationKey = this.key(symbol1, symbol2);
                    CorrelationResult result = this.results.get(correlationKey);
                    writer.print("\"" + SQUtils.d2((double)result.value) + "\"");
                    if (j == this.symbolList.size() - 1) continue;
                    writer.print(";");
                }
                writer.println();
            }
            writer.flush();
            writer.close();
        }
        catch (Exception e) {
            Log.error("Error while saving Correlation matrix to csv.", (Throwable)e);
            throw new Exception(L.t((String)"Cannot save Correlation matrix to csv - %s", (Object[])new Object[]{e.getMessage()}));
        }
    }

    private String getColor(double value) {
        try {
            if (value < 0.0) {
                if (this.allowNegativeCorrelation) {
                    return "#00ff00";
                }
                value = Math.abs(value);
            }
            int n = (int)(value * 100.0);
            int r = 255 * n / 100;
            int g = 255 * (100 - n) / 100;
            int b = 0;
            return String.format("#%02x%02x%02x", r, g, b);
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            return "#FFFFFF";
        }
    }

    private String getTextColor(double value) {
        try {
            if (value < 0.0) {
                if (this.allowNegativeCorrelation) {
                    return "#0000ff";
                }
                value = Math.abs(value);
            }
            int r = value < 0.3 ? 0 : 255;
            int g = value < 0.3 ? 0 : 255;
            int b = 255;
            return String.format("#%02x%02x%02x", r, g, b);
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            return "#FFFFFF";
        }
    }

    private String getColor2(double value) {
        if (value < 0.0) {
            return "#ff0000";
        }
        if (value > 0.0) {
            return "#00ff00";
        }
        return "#000000";
    }

    public void stop() {
        this.stopped = true;
    }

    public void clear() {
        this.results.clear();
        if (this.periods != null) {
            this.periods = null;
        }
    }
}

