/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  com.strategyquant.datalib.ticksimulator.SpreadsMap
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQUtils
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.datalib.ticksimulator.SpreadsMap;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtest.BacktestConnection;
import com.strategyquant.tradinglib.backtest.BacktestDataCache;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.LoadedData;
import com.strategyquant.tradinglib.backtest.StartDataInfo;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.engine.BacktestTradingSetup;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.robustnesstests.DataModifierCallback;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.setup.Portfolio;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestDataFeed {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestDataFeed");
    private ConnectionManager connectionManager;
    volatile LoadedData loadedData = null;
    private BacktestTradingSetup[] tradingSetups;
    private ITradingSimulator defaultTradingSimulator;
    private StartDataInfo startDataInfo = new StartDataInfo();
    private int backtestPrecision;
    private ITradingSimulator[] tradingSimulators;
    private BacktestDataCache backtestDataCache = BacktestDataCache.getInstance();
    protected TickEvent tick = new TickEvent();
    protected long lastIndex;
    private DataModifierCallback dataModifierCallback = null;
    private StopPauseEngine stopPauseEngine;
    private SpreadsMap spreadsMap;
    private LoadDataProgressEngine loadDataProgressEngine;
    private int barEventType;
    private long totalTicks = 0L;
    private OutOfSample outOfSampleSettings;
    private boolean trading = true;

    public BacktestDataFeed(int n, ConnectionManager connectionManager, ITradingSimulator iTradingSimulator, ITradingSimulator[] iTradingSimulatorArray) throws Exception {
        this.backtestPrecision = n;
        this.connectionManager = connectionManager;
        this.defaultTradingSimulator = iTradingSimulator;
        this.tradingSimulators = iTradingSimulatorArray;
    }

    public void initialize(Portfolio portfolio, ITradingSimulator iTradingSimulator, OutOfSample outOfSample) throws Exception {
        this.setPortfolio(portfolio);
        this.loadDataForFeed(iTradingSimulator, outOfSample);
    }

    private void loadDataForFeed(ITradingSimulator iTradingSimulator, OutOfSample outOfSample) throws Exception {
        this.loadedData = null;
        this.backtestDataCache.setLoadDataProgressEngine(this.loadDataProgressEngine);
        ArrayList<ChartDef> arrayList = this.getAllBacktestChartDefs();
        this.spreadsMap = new SpreadsMap(arrayList);
        this.loadedData = this.backtestDataCache.loadData(this.tradingSetups, arrayList, this.spreadsMap, this.backtestPrecision, iTradingSimulator);
        this.setOOS(outOfSample);
        MarketData[] marketDataArray = this.loadedData.getMarketData();
        if (marketDataArray == null || marketDataArray.length != this.tradingSetups.length) {
            throw new Exception(L.t((String)"Prepared MarketData array doesn't have as same size as TradingSetups!", (Object[])new Object[0]));
        }
        for (int i = 0; i < this.tradingSetups.length; ++i) {
            this.tradingSetups[i].setLoadedMarketData(marketDataArray[i]);
        }
        this.totalTicks = this.loadedData.size();
    }

    private void setOOS(OutOfSample outOfSample) {
        this.outOfSampleSettings = outOfSample;
    }

    public void start() throws Exception {
        long l = System.currentTimeMillis();
        VersatileData versatileData = new VersatileData();
        TickEvent tickEvent = new TickEvent();
        ITickSimulator iTickSimulator = this.defaultTradingSimulator.getTickSimulator();
        iTickSimulator.setSymbolsSpread(this.spreadsMap);
        this.barEventType = this.defaultTradingSimulator.getBarEventType();
        long l2 = 0L;
        this.trading = true;
        while ((versatileData = this.loadedData.getNextTick(versatileData)) != null) {
            if (this.stopPauseEngine != null && this.stopPauseEngine.isStopped()) {
                this.loadedData.destroy();
                long l3 = System.currentTimeMillis();
                if (Log.isDebugEnabled()) {
                    Log.debug(String.format("BACKTEST DATA FEED STOPPED %d ms, ticks: %d", l3 - l, this.loadedData.size()));
                }
                for (ITradingSimulator iTradingSimulator : this.tradingSimulators) {
                    iTradingSimulator.eventEndOfTest();
                }
                return;
            }
            if (versatileData.type == 1) {
                if (this.backtestPrecision != 4 && this.backtestPrecision != 5) {
                    double d = this.spreadsMap.getSpread(versatileData.connectionHash + versatileData.symbolHash);
                    versatileData.ask = d == -1.0 ? versatileData.ask : SQUtils.round7((double)(versatileData.bid + d));
                }
                tickEvent.set(versatileData.time, versatileData.connectionHash, versatileData.symbolHash, versatileData.bid, versatileData.ask, versatileData.volume, versatileData.sessionStartTime, false, false);
                if (this.dataModifierCallback != null) {
                    this.dataModifierCallback.modifyData(tickEvent);
                }
                ++l2;
                this.processEvent(tickEvent, 0.0, 0.0);
                continue;
            }
            if (this.dataModifierCallback != null) {
                this.dataModifierCallback.modifyOHLCData(versatileData);
            }
            iTickSimulator.init(versatileData);
            while (iTickSimulator.getNextTick(tickEvent)) {
                if (this.dataModifierCallback != null) {
                    this.dataModifierCallback.modifyData(tickEvent);
                }
                ++l2;
                this.processEvent(tickEvent, versatileData.high, versatileData.low);
            }
        }
        for (ITradingSimulator iTradingSimulator : this.tradingSimulators) {
            iTradingSimulator.eventEndOfTest();
        }
        this.loadedData.destroy();
        long l4 = System.currentTimeMillis();
        if (Log.isDebugEnabled()) {
            Log.debug(String.format("SEND TOOK: %d ms, ticks: %d", l4 - l, l2));
        }
    }

    private void processEvent(TickEvent tickEvent, double d, double d2) throws Exception {
        int n;
        ITradingSimulator[] iTradingSimulatorArray;
        if (this.outOfSampleSettings != null && this.outOfSampleSettings.hasNoTrade()) {
            if (this.trading) {
                if (this.outOfSampleSettings.isNoTrade(tickEvent.getTime())) {
                    this.trading = false;
                    iTradingSimulatorArray = this.tradingSimulators;
                    int n2 = iTradingSimulatorArray.length;
                    for (n = 0; n < n2; ++n) {
                        ITradingSimulator iTradingSimulator = iTradingSimulatorArray[n];
                        iTradingSimulator.eventNoTrade();
                    }
                }
            } else if (!this.outOfSampleSettings.isNoTrade(tickEvent.getTime())) {
                this.trading = true;
            }
        }
        if (this.barEventType != 3 && this.trading) {
            for (int i = 0; i < this.tradingSimulators.length; ++i) {
                this.tradingSimulators[i].eventNewTick(tickEvent, d, d2);
            }
        }
        BarUpdateInfo barUpdateInfo = null;
        for (n = 0; n < this.tradingSetups.length; ++n) {
            iTradingSimulatorArray = this.tradingSetups[n];
            iTradingSimulatorArray.processEvent(tickEvent, this.trading);
            if (n == 0) {
                barUpdateInfo = iTradingSimulatorArray.getBarUpdateInfo();
            }
            if (iTradingSimulatorArray.getTradingException() == null) continue;
            throw iTradingSimulatorArray.getTradingException();
        }
        if (this.barEventType == 3) {
            if (barUpdateInfo.eventType == 5 && barUpdateInfo.mainChartEventType != -1) {
                barUpdateInfo.eventType = barUpdateInfo.mainChartEventType;
            }
            if (this.trading) {
                for (n = 0; n < this.tradingSimulators.length; ++n) {
                    this.tradingSimulators[n].eventNewTick(tickEvent, d, d2, barUpdateInfo);
                }
            }
        }
    }

    public void setPortfolio(Portfolio portfolio) throws Exception {
        ArrayList<TradingSetup> arrayList = portfolio.getTradingSetups();
        this.tradingSetups = new BacktestTradingSetup[arrayList.size()];
        int n = 0;
        for (TradingSetup tradingSetup : portfolio.getTradingSetups()) {
            this.createConnectionsForSetup(tradingSetup.getChartSetup());
            tradingSetup.getChartSetup().runChecks(this.connectionManager);
            this.tradingSetups[n++] = (BacktestTradingSetup)tradingSetup;
        }
        for (BacktestTradingSetup backtestTradingSetup : this.tradingSetups) {
            backtestTradingSetup.setBarEventType(this.defaultTradingSimulator.getBarEventType());
        }
    }

    private void createConnectionsForSetup(ChartSetup chartSetup) throws DataException {
        for (ChartDef chartDef : chartSetup.getCharts()) {
            String string = chartDef.getConnectionName();
            if (this.connectionManager.hasConnection(string)) continue;
            BacktestConnection backtestConnection = new BacktestConnection(string, this);
            this.connectionManager.addConnection(string, backtestConnection);
        }
    }

    public void setDataModifierCallback(DataModifierCallback dataModifierCallback) {
        this.dataModifierCallback = dataModifierCallback;
    }

    public void setStopPauseEngine(StopPauseEngine stopPauseEngine) {
        this.stopPauseEngine = stopPauseEngine;
    }

    public ArrayList<ChartDef> getAllBacktestChartDefs() throws Exception {
        ArrayList<ChartDef> arrayList = new ArrayList<ChartDef>();
        for (BacktestTradingSetup backtestTradingSetup : this.tradingSetups) {
            ArrayList<ChartDef> arrayList2 = backtestTradingSetup.getChartSetup().getCharts();
            for (int i = 0; i < arrayList2.size(); ++i) {
                ChartDef chartDef = arrayList2.get(i);
                if (i == 0) {
                    this.backtestDataCache.getRealStartDataInfo(chartDef, backtestTradingSetup.getReservedBars(), this.defaultTradingSimulator, this.startDataInfo);
                    backtestTradingSetup.setReservedBars(this.startDataInfo.reservedBars);
                }
                chartDef.setLoadedHistoryFrom(this.startDataInfo.realDataStartTime);
                arrayList.add(new ChartDef(chartDef));
            }
        }
        return arrayList;
    }

    public void setLoadDataProgressEngine(LoadDataProgressEngine loadDataProgressEngine) {
        this.loadDataProgressEngine = loadDataProgressEngine;
    }

    public long getTotalTicks() {
        return this.totalTicks;
    }

    public MarketData getMarketData() {
        if (this.loadedData == null) {
            return null;
        }
        MarketData[] marketDataArray = this.loadedData.getMarketData();
        if (marketDataArray == null || marketDataArray.length == 0) {
            return null;
        }
        return marketDataArray[0];
    }
}

