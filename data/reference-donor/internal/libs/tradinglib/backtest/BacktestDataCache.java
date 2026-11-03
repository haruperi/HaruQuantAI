/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.ticksimulator.SpreadsMap
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.TaskStoppedException
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.ticksimulator.SpreadsMap;
import com.strategyquant.lib.L;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.backtest.BacktestRealDataStartTimeComputer;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.LoadedData;
import com.strategyquant.tradinglib.backtest.StartDataInfo;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.engine.BacktestTradingSetup;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.io.File;
import java.util.ArrayList;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestDataCache {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestDataCache");
    private static BacktestDataCache instance;
    private long cacheRecordsSize = 1000000L;
    private ConcurrentHashMap<Integer, LoadedData> mapCache = new ConcurrentHashMap();
    private Int2ObjectOpenHashMap<StartDataInfo> startDataInfoCache = new Int2ObjectOpenHashMap();
    private int dataType = 0;
    private LoadDataProgressEngine loadDataProgressEngine;
    private StampedLock cacheLock = new StampedLock();

    public static synchronized BacktestDataCache getInstance() {
        if (instance == null) {
            instance = new BacktestDataCache();
        }
        return instance;
    }

    public LoadedData loadData(BacktestTradingSetup[] backtestTradingSetupArray, ArrayList<ChartDef> arrayList, SpreadsMap spreadsMap, int n, ITradingSimulator iTradingSimulator) throws Exception {
        int n2 = this.computeHash(arrayList, n, backtestTradingSetupArray);
        LoadedData loadedData = null;
        Exception exception = null;
        LoadDataProgressEngine loadDataProgressEngine = this.loadDataProgressEngine;
        if (loadDataProgressEngine != null) {
            loadDataProgressEngine.printToLog(L.t((String)"Loading backtest data for %s - %s", (Object[])new Object[]{loadDataProgressEngine.getTestName(), loadDataProgressEngine.getSymbolTF()}));
        }
        try {
            loadedData = this._loadData(n2, backtestTradingSetupArray, arrayList, spreadsMap, n, iTradingSimulator);
            return loadedData;
        }
        catch (TaskStoppedException taskStoppedException) {
            Log.info("Loading data stopped");
            this.mapCache.remove(n2);
            throw taskStoppedException;
        }
        catch (Exception exception2) {
            Log.error("Exception when loading data", (Throwable)exception2);
            exception = exception2;
            String string = TestfilesUtils.getTestdataFile(n2);
            File file = new File(string);
            if (file.exists()) {
                if (!file.delete()) {
                    throw new Exception(L.t((String)"Cannot delete corrupted data file '%s'", (Object[])new Object[]{string}), exception);
                }
                this.mapCache.remove(n2);
                Log.info("Deleted corrupted data file {}, regenerating it again", (Object)string);
            }
            try {
                loadedData = this._loadData(n2, backtestTradingSetupArray, arrayList, spreadsMap, n, iTradingSimulator);
            }
            catch (TaskStoppedException taskStoppedException) {
                Log.info("Loading data stopped");
                throw taskStoppedException;
            }
            catch (Exception exception3) {
                Log.error("Exception when loading data", (Throwable)exception3);
                exception = exception3;
            }
            return loadedData;
        }
    }

    private LoadedData _loadData(int n, BacktestTradingSetup[] backtestTradingSetupArray, ArrayList<ChartDef> arrayList, SpreadsMap spreadsMap, int n2, ITradingSimulator iTradingSimulator) throws Exception {
        LoadedData loadedData = this.mapCache.computeIfAbsent(n, n3 -> this.createLoadedData(n, this.dataType, backtestTradingSetupArray, arrayList, spreadsMap, n2, iTradingSimulator, this.loadDataProgressEngine));
        if (loadedData == null) {
            this.mapCache.remove(n);
            throw new Exception(L.t((String)"Loaded data is null", (Object[])new Object[0]));
        }
        if (loadedData.getException() != null) {
            this.mapCache.remove(n);
            throw loadedData.getException();
        }
        if (!loadedData.isJustCreated()) {
            LoadedData loadedData2 = new LoadedData(loadedData, this.loadDataProgressEngine);
            loadedData2.setLoadStats(loadedData.getLoadStats());
            loadedData.resetLoadStats();
            return loadedData2;
        }
        loadedData.setNotJustCreated();
        return loadedData;
    }

    private LoadedData createLoadedData(int n, int n2, BacktestTradingSetup[] backtestTradingSetupArray, ArrayList<ChartDef> arrayList, SpreadsMap spreadsMap, int n3, ITradingSimulator iTradingSimulator, LoadDataProgressEngine loadDataProgressEngine) {
        LoadedData loadedData = new LoadedData(n, n2);
        loadedData.trackUsed();
        try {
            loadedData.load(backtestTradingSetupArray, arrayList, spreadsMap, n3, iTradingSimulator, loadDataProgressEngine);
        }
        catch (Exception exception) {
            // empty catch block
        }
        return loadedData;
    }

    private int computeHash(ArrayList<ChartDef> arrayList, int n, BacktestTradingSetup[] backtestTradingSetupArray) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(n);
        for (ChartDef chartDef : arrayList) {
            stringBuilder.append(chartDef.getChartsHash());
        }
        for (BacktestTradingSetup backtestTradingSetup : backtestTradingSetupArray) {
            stringBuilder.append(backtestTradingSetup.getChartsHash());
        }
        int n2 = stringBuilder.toString().hashCode();
        return n2;
    }

    public synchronized void getRealStartDataInfo(ChartDef chartDef, int n, ITradingSimulator iTradingSimulator, StartDataInfo startDataInfo) throws Exception {
        StartDataInfo startDataInfo2;
        int n2 = chartDef.getChartsHash().hashCode() + iTradingSimulator.getClass().getName().hashCode();
        if (!this.startDataInfoCache.containsKey(n2)) {
            startDataInfo2 = new StartDataInfo();
            this.getRealDataStartTime(chartDef, n, iTradingSimulator, startDataInfo2);
            this.startDataInfoCache.put(n2, (Object)startDataInfo2);
        } else {
            startDataInfo2 = (StartDataInfo)this.startDataInfoCache.get(n2);
        }
        startDataInfo.copyFrom(startDataInfo2);
    }

    private void getRealDataStartTime(ChartDef chartDef, int n, ITradingSimulator iTradingSimulator, StartDataInfo startDataInfo) throws Exception {
        ReservedBarsType reservedBarsType = iTradingSimulator.getReservedBarsType();
        if (reservedBarsType.type == 2) {
            startDataInfo.realDataStartTime = chartDef.getHistoryFrom();
            startDataInfo.reservedBars = Math.max(reservedBarsType.minimumReservedBars, n);
        }
        BacktestRealDataStartTimeComputer backtestRealDataStartTimeComputer = new BacktestRealDataStartTimeComputer(n, chartDef, iTradingSimulator);
        backtestRealDataStartTimeComputer.computeRealDataStartTime(startDataInfo, this.loadDataProgressEngine);
        backtestRealDataStartTimeComputer.destroy();
    }

    public void setDataType(int n) {
        this.dataType = n;
    }

    public void setLoadDataProgressEngine(LoadDataProgressEngine loadDataProgressEngine) {
        this.loadDataProgressEngine = loadDataProgressEngine;
    }

    public synchronized long freeCache() {
        return 0L;
    }

    public void deleteTempTestfile(String string) {
        TestfilesUtils.deleteTempTestfile(string);
    }
}

