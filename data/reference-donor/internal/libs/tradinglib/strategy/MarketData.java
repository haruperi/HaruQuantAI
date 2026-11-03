/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.InstrumentInfo
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.bartype.BarType
 *  com.strategyquant.datalib.bartype.BarTypeFactory
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.datalib.ticksimulator.DefaultTickSimulator
 *  com.strategyquant.lib.time.SQTimeOld
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.strategy;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.InstrumentInfo;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.bartype.BarType;
import com.strategyquant.datalib.bartype.BarTypeFactory;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.datalib.ticksimulator.DefaultTickSimulator;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartData;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.connection.HistoryData;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.strategy.PreparedChartData;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MarketData {
    public static final Logger Log = LoggerFactory.getLogger((String)"MarketData");
    protected ChartData[] chartData;
    protected TradingSetup tradingSetup;
    protected ChartSetup chartSetup;
    private Int2ObjectOpenHashMap<ChartData> chartDatasBySymbol = new Int2ObjectOpenHashMap();
    private int indyStartingBar;

    public MarketData(TradingSetup tradingSetup, ChartSetup chartSetup) throws Exception {
        this(tradingSetup, chartSetup, 0);
    }

    public MarketData(TradingSetup tradingSetup, ChartSetup chartSetup, int n) throws Exception {
        this.tradingSetup = tradingSetup;
        this.chartSetup = chartSetup;
        this.indyStartingBar = n;
        this.initializeChartData();
    }

    protected MarketData() {
        boolean bl;
        boolean bl2 = bl = true;
    }

    private void initializeChartData() throws Exception {
        ArrayList<ChartDef> arrayList = this.chartSetup.getCharts();
        this.chartData = new ChartData[arrayList.size()];
        int n = 0;
        for (ChartDef chartDef : arrayList) {
            this.chartData[n] = new ChartData(this, chartDef, n, this.chartSetup.getBacktestEngine());
            this.chartData[n].setIndyStartingBar(this.getIndyStartingBar());
            ++n;
        }
    }

    public ChartData Chart(int n) {
        return this.chartData[n];
    }

    public ChartData Chart(String string) throws TradingException {
        if (string.equals("Current")) {
            return this.chartData[0];
        }
        int n = string.hashCode();
        for (ChartData chartData : this.chartData) {
            if (chartData.getSymbolHash() != n) continue;
            return chartData;
        }
        throw new TradingException(String.format("Chart for symbol '%s' was not found!", string));
    }

    public void addChart(String string) throws Exception {
        this.addChart(this.chartData[0].Connection, this.chartData[0].Symbol, string);
    }

    public void addChart(String string, String string2) throws Exception {
        this.addChart(this.chartData[0].Connection, string, string2);
    }

    public void addChart(String string, String string2, String string3) throws Exception {
        if (!this.tradingSetup.isInInit()) {
            throw new TradingException("You cannot call MarketData.addChart() outside the Strategy.onInit() method !");
        }
        ChartDef chartDef = this.chartSetup.addChart(string, string2, string3);
        this.chartData = Arrays.copyOf(this.chartData, this.chartData.length + 1);
        this.chartData[this.chartData.length - 1] = new ChartData(this, chartDef, this.chartData.length - 1, this.chartSetup.getBacktestEngine());
    }

    public int getChartsCount() {
        return this.chartSetup.getChartsCount();
    }

    public boolean processTick(TickEvent tickEvent, BarUpdateInfo barUpdateInfo, int n) throws Exception {
        if (this.chartData.length == 0) {
            return false;
        }
        int n2 = 0;
        boolean bl = false;
        for (int i = 0; i < this.chartData.length; ++i) {
            ChartData chartData = this.chartData[i];
            chartData.processTick(tickEvent, n, this.chartData.length);
            if (chartData.EventType == 1) continue;
            ++n2;
            if (i == 0) {
                barUpdateInfo.updatedMainChart = true;
            }
            if (barUpdateInfo.updatedChart < 0) {
                barUpdateInfo.updatedChart = i;
                barUpdateInfo.eventType = chartData.EventType;
            }
            if (chartData.EventType != n) continue;
            bl = true;
        }
        if (n2 > 1) {
            barUpdateInfo.multipleChartsUpdated = true;
            barUpdateInfo.updatedChart = -1;
            barUpdateInfo.eventType = 5;
        }
        return bl;
    }

    public boolean findTickInData(TickEvent tickEvent, BarUpdateInfo barUpdateInfo, int n, boolean bl) throws Exception {
        return this.findTickInData(tickEvent, barUpdateInfo, n, bl, true);
    }

    public boolean findTickInData(TickEvent tickEvent, BarUpdateInfo barUpdateInfo, int n, boolean bl, boolean bl2) throws Exception {
        if (this.chartData.length == 0) {
            return false;
        }
        int n2 = 0;
        boolean bl3 = false;
        barUpdateInfo.mainChartEventType = -1;
        if (this.chartData.length == 1) {
            ChartData chartData = this.chartData[0];
            chartData.findTickInData(tickEvent, n, bl, bl2, 0);
            if (chartData.EventType != 1) {
                ++n2;
                barUpdateInfo.updatedMainChart = true;
                if (barUpdateInfo.updatedChart <= 0) {
                    barUpdateInfo.updatedChart = 0;
                    barUpdateInfo.eventType = chartData.EventType;
                }
                if (chartData.EventType == n) {
                    bl3 = true;
                }
            }
        } else {
            for (int i = 0; i < this.chartData.length; ++i) {
                ChartData chartData = this.chartData[i];
                chartData.findTickInData(tickEvent, n, bl, bl2, i);
                if (chartData.EventType == 1) continue;
                ++n2;
                if (i == 0) {
                    barUpdateInfo.updatedMainChart = true;
                    barUpdateInfo.mainChartEventType = chartData.EventType;
                }
                if (barUpdateInfo.updatedChart <= 0) {
                    barUpdateInfo.updatedChart = i;
                    barUpdateInfo.eventType = chartData.EventType;
                }
                if (chartData.EventType != n) continue;
                bl3 = true;
            }
            if (n2 > 1) {
                barUpdateInfo.multipleChartsUpdated = true;
                barUpdateInfo.updatedChart = -1;
                barUpdateInfo.eventType = 5;
            }
        }
        return bl3;
    }

    public void requestHistoryData(ConnectionManager connectionManager, int n) throws Exception {
        SQTimeOld sQTimeOld = new SQTimeOld();
        ChartDef chartDef = this.chartSetup.getCharts().get(0);
        long l = this.recognizeStartTime(chartDef, sQTimeOld);
        HashMap<String, HistoryData> hashMap = this.loadHistoryData(connectionManager, l, sQTimeOld);
        this.fillMarketData(hashMap);
        Log.debug("Load history data finished");
    }

    private void fillMarketData(HashMap<String, HistoryData> hashMap) throws Exception {
        DefaultTickSimulator defaultTickSimulator = new DefaultTickSimulator();
        TickEvent tickEvent = new TickEvent();
        for (HistoryData historyData : hashMap.values()) {
            if (historyData == null) continue;
            for (VersatileData versatileData : historyData.getData()) {
                defaultTickSimulator.init(versatileData);
                while (defaultTickSimulator.getNextTick(tickEvent)) {
                    for (int i = 0; i < this.chartData.length; ++i) {
                        ChartData chartData = this.chartData[i];
                        chartData.processTickSimplified(tickEvent, this.chartData.length);
                    }
                }
            }
        }
    }

    private HashMap<String, HistoryData> loadHistoryData(ConnectionManager connectionManager, long l, SQTimeOld sQTimeOld) throws DataException {
        HashMap<String, HistoryData> hashMap = new HashMap<String, HistoryData>();
        for (ChartDef chartDef : this.chartSetup.getCharts()) {
            String string = chartDef.getConnectionName() + "_" + chartDef.getSymbol();
            if (hashMap.containsKey(string)) continue;
            Connection connection = connectionManager.getConnection(chartDef.getConnectionName());
            if (!connection.isDataFeed()) {
                throw new DataException(1, "Connection '" + connection.getConnectionName() + "' is not a Data Feed !");
            }
            HistoryData historyData = connection.getDataFeed().getHistoryData(chartDef, 1, l, sQTimeOld.getMilis());
            hashMap.put(string, historyData);
        }
        return hashMap;
    }

    long recognizeStartTime(ChartDef chartDef, SQTimeOld sQTimeOld) throws DataException {
        if (chartDef.getBackloadType() == 1) {
            SQTimeOld sQTimeOld2 = sQTimeOld.addDaysReturnDate((int)((double)((int)chartDef.getBackloadNumber()) * 1.3));
            return sQTimeOld2.getMilis();
        }
        if (chartDef.getBackloadType() == 2) {
            BarType barType = BarTypeFactory.getBarType((String)chartDef.getTimeframe(), (int)chartDef.getBarTimeType());
            long l = barType.estimateStartDate((int)chartDef.getBackloadNumber() + 200, sQTimeOld.getMilis());
            if (l == 0L) {
                SQTimeOld sQTimeOld3 = sQTimeOld.addDaysReturnDate(-100);
                l = sQTimeOld3.getMilis();
            }
            return l;
        }
        if (chartDef.getBackloadType() == 3) {
            return SQTimeOld.correctDayStart((long)chartDef.getBackloadNumber());
        }
        return 0L;
    }

    public void destroy() {
        if (this.chartData == null) {
            return;
        }
        for (ChartData chartData : this.chartData) {
            chartData.destroy();
        }
        this.chartData = null;
    }

    public ChartData[] getChartData() {
        return this.chartData;
    }

    public InstrumentInfo getInstrumentInfo(String string) {
        if (string.equals("Current")) {
            return this.chartData[0].getInstrumentInfo();
        }
        int n = string.hashCode();
        if (this.chartDatasBySymbol.containsKey(n)) {
            return ((ChartData)this.chartDatasBySymbol.get(n)).getInstrumentInfo();
        }
        for (ChartData chartData : this.chartData) {
            if (chartData.getSymbolHash() != n) continue;
            this.chartDatasBySymbol.put(n, (Object)chartData);
            return chartData.getInstrumentInfo();
        }
        return null;
    }

    public long Time(int n) throws TradingException {
        return this.chartData[0].Time(n);
    }

    public double Open(int n) throws TradingException {
        return this.chartData[0].Open(n);
    }

    public double High(int n) throws TradingException {
        return this.chartData[0].High(n);
    }

    public double Low(int n) throws TradingException {
        return this.chartData[0].Low(n);
    }

    public double Close(int n) throws TradingException {
        return this.chartData[0].Close(n);
    }

    public double Volume(int n) throws TradingException {
        return this.chartData[0].Volume(n);
    }

    public long TimeCurrent() throws TradingException {
        return this.chartData[0].TimeCurrent();
    }

    public MarketData cloneToPrepared(TradingSetup tradingSetup, ChartSetup chartSetup, int n) throws Exception {
        MarketData marketData = new MarketData();
        marketData.tradingSetup = tradingSetup;
        marketData.chartSetup = chartSetup;
        if (n > 0) {
            marketData.indyStartingBar = n;
        }
        marketData.chartData = new ChartData[this.chartData.length];
        ArrayList<ChartDef> arrayList = chartSetup.getCharts();
        if (arrayList.size() != this.chartData.length) {
            throw new Exception("ChartDefs size is not as same as prepared chart data size !");
        }
        for (int i = 0; i < this.chartData.length; ++i) {
            marketData.chartData[i] = new PreparedChartData(this.chartData[i], marketData, tradingSetup, arrayList.get(i), n);
        }
        return marketData;
    }

    public void setPerformanceParams(boolean bl, boolean bl2, boolean bl3, boolean bl4) {
        for (int i = 0; i < this.chartData.length; ++i) {
            this.chartData[i].setPerformanceParams(bl, bl2, bl3, bl4);
        }
    }

    public boolean isNextDay(TickEvent tickEvent) {
        if (this.chartData.length == 0) {
            return false;
        }
        ChartData chartData = this.chartData[0];
        return chartData.isNextDay(tickEvent);
    }

    public int getIndyStartingBar() {
        return this.indyStartingBar;
    }

    public long getDateBarsFromDate(long l, int n) {
        TimeDataSeries timeDataSeries = this.chartData[0].Time;
        if (timeDataSeries == null) {
            return 0L;
        }
        long l2 = timeDataSeries.getDateBarsFromDate(l, n);
        return l2;
    }
}

