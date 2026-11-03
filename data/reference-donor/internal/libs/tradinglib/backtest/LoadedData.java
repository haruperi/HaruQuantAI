/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataSeries
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.dataseries.TimeDataSeries
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.session.SessionStatus
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  com.strategyquant.datalib.ticksimulator.SpreadsMap
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataSeries;
import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.dataseries.TimeDataSeries;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.datalib.ticksimulator.SpreadsMap;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.backtest.DataLoadStats;
import com.strategyquant.tradinglib.backtest.FeedDataCreator;
import com.strategyquant.tradinglib.backtest.HashPair;
import com.strategyquant.tradinglib.backtest.ILoadedDataHolder;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtest.LoadedDataHolderFileBDF;
import com.strategyquant.tradinglib.backtest.LoadedDataHolderOffheap;
import com.strategyquant.tradinglib.backtest.TestfilesUtils;
import com.strategyquant.tradinglib.engine.BacktestTradingSetup;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.strategy.MarketData;
import com.strategyquant.tradinglib.strategy.OutOfSample;
import java.io.File;
import java.lang.management.ManagementFactory;
import java.lang.management.MemoryMXBean;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class LoadedData {
    public static final Logger Log = LoggerFactory.getLogger((String)"LoadedData");
    private ILoadedDataHolder loadedDataHolder = null;
    private DataLoadStats dataLoadStats = new DataLoadStats();
    private int hash;
    private Exception loadException = null;
    private int usedCounter = 0;
    private long lastTimeUsed = 0L;
    private boolean justCreated;
    private int dataType;
    protected final MemoryMXBean memoryBean = ManagementFactory.getMemoryMXBean();
    private OutOfSample outOfSampleSettings;

    public LoadedData(int n, int n2) {
        this.hash = n;
        this.dataType = n2;
        this.justCreated = true;
    }

    public LoadedData(LoadedData loadedData, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        this.hash = loadedData.hash;
        this.dataType = loadedData.dataType;
        if (loadedData.loadException != null) {
            throw loadedData.loadException;
        }
        if (loadDataProgressEngine != null) {
            loadDataProgressEngine.printToLog(L.t((String)"Data loaded from memory", (Object[])new Object[0]));
            loadDataProgressEngine.onDataPreparationFinished(0.0, loadedData.size());
        }
        this.loadedDataHolder = loadedData.loadedDataHolder.cloneHolder();
        this.justCreated = false;
    }

    public long size() throws Exception {
        return this.loadedDataHolder.size();
    }

    public VersatileData getNextTick(VersatileData versatileData) throws Exception {
        return this.loadedDataHolder.getNextTick(versatileData);
    }

    public DataLoadStats getLoadStats() {
        return this.dataLoadStats;
    }

    public void setLoadStats(DataLoadStats dataLoadStats) {
        this.dataLoadStats.ticks = dataLoadStats.ticks;
        this.dataLoadStats.loadingTime = dataLoadStats.loadingTime;
    }

    public void resetLoadStats() {
        this.dataLoadStats.ticks = -1;
        this.dataLoadStats.loadingTime = 0L;
    }

    public void load(BacktestTradingSetup[] backtestTradingSetupArray, ArrayList<ChartDef> arrayList, SpreadsMap spreadsMap, int n, ITradingSimulator iTradingSimulator, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        try {
            Object object;
            LoadedDataHolderFileBDF loadedDataHolderFileBDF = new LoadedDataHolderFileBDF(this.hash);
            if (!loadedDataHolderFileBDF.isLoaded()) {
                object = new FeedDataCreator();
                try {
                    loadedDataHolderFileBDF.beforeSave(this.computeHashPairs(arrayList));
                    ((FeedDataCreator)object).loadFeed(arrayList, n, this.dataLoadStats, loadedDataHolderFileBDF, loadDataProgressEngine);
                    loadedDataHolderFileBDF.afterSave();
                }
                catch (TaskStoppedException taskStoppedException) {
                    loadedDataHolderFileBDF.close();
                    String string = TestfilesUtils.getTestdataFile(this.hash);
                    File file = new File(string);
                    if (file.exists()) {
                        if (!file.delete()) {
                            Log.info("Cannot delete unfinished data file {}", (Object)string);
                        } else {
                            Log.info("Deleted unfinished data file {}, will be created again", (Object)string);
                        }
                    }
                    throw taskStoppedException;
                }
                catch (Exception exception) {
                    loadedDataHolderFileBDF.close();
                    throw exception;
                }
            }
            try {
                object = loadedDataHolderFileBDF;
                if (LoadedDataHolderOffheap.isEnoughMemory(this.hash, this.memoryBean)) {
                    object = new LoadedDataHolderOffheap(this.hash, loadedDataHolderFileBDF, this.dataLoadStats, loadDataProgressEngine);
                    loadedDataHolderFileBDF.close();
                }
            }
            catch (Exception exception) {
                loadedDataHolderFileBDF.close();
                throw exception;
            }
            catch (OutOfMemoryError outOfMemoryError) {
                Log.info("Switching back to file-based data holder");
                object = loadedDataHolderFileBDF.cloneHolder();
            }
            if (object instanceof LoadedDataHolderOffheap && object.size() <= 0L) {
                throw new Exception(L.t((String)"Data are empty - there could be problem with data source or sessions.", (Object[])new Object[0]));
            }
            MarketData[] marketDataArray = this.prepareMarketData(backtestTradingSetupArray, spreadsMap, (ILoadedDataHolder)object, iTradingSimulator, loadDataProgressEngine);
            this.loadedDataHolder = object.cloneHolder();
            this.loadedDataHolder.setMarketData(marketDataArray);
        }
        catch (Exception exception) {
            this.loadException = exception;
            throw exception;
        }
    }

    private void exportToFile(String string, TimeDataSeries timeDataSeries, DataSeries dataSeries) throws TradingException {
        StringBuilder stringBuilder = new StringBuilder();
        for (int i = timeDataSeries.size() - 1; i >= 0; --i) {
            stringBuilder.append(SQTime.toDateMinuteString((long)timeDataSeries.get(i)));
            stringBuilder.append(";");
            stringBuilder.append(dataSeries.get(i));
            stringBuilder.append("\n");
        }
        SQUtils.stringToFile((File)new File("d:/temp3/exp/" + string + ".txt"), (String)stringBuilder.toString());
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    private MarketData[] prepareMarketData(BacktestTradingSetup[] backtestTradingSetupArray, SpreadsMap spreadsMap, ILoadedDataHolder iLoadedDataHolder, ITradingSimulator iTradingSimulator, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        long l = System.currentTimeMillis();
        MarketData[] marketDataArray = new MarketData[backtestTradingSetupArray.length];
        for (int i = 0; i < backtestTradingSetupArray.length; ++i) {
            marketDataArray[i] = new MarketData(null, backtestTradingSetupArray[i].getChartSetup().getClone(), backtestTradingSetupArray[i].getIndyStartingBar());
            marketDataArray[i].setPerformanceParams(false, false, false, false);
        }
        ITickSimulator iTickSimulator = iTradingSimulator.getTickSimulator();
        iTickSimulator.setSymbolsSpread(spreadsMap);
        VersatileData versatileData = new VersatileData();
        TickEvent tickEvent = new TickEvent();
        BarUpdateInfo barUpdateInfo = new BarUpdateInfo();
        String string = backtestTradingSetupArray[0].getChartSetup().getMainChart().getSession();
        Session session = SessionManager.getSession((String)string);
        if (session == null) {
            session = SessionManager.getSession((String)"No Session");
        }
        session.clearSessionTempData();
        SessionStatus sessionStatus = new SessionStatus();
        try {
            while ((versatileData = iLoadedDataHolder.getNextTick(versatileData)) != null) {
                if (versatileData.type == 1) {
                    double d = spreadsMap.getSpread(versatileData.connectionHash + versatileData.symbolHash);
                    versatileData.ask = d == -1.0 ? versatileData.ask : SQUtils.round7((double)(versatileData.bid + d));
                    tickEvent.set(versatileData.time, versatileData.connectionHash, versatileData.symbolHash, versatileData.bid, versatileData.ask, versatileData.volume, versatileData.sessionStartTime, false, false);
                    barUpdateInfo.updatedChart = -1;
                    barUpdateInfo.multipleChartsUpdated = false;
                    barUpdateInfo.eventType = 1;
                    for (int i = 0; i < backtestTradingSetupArray.length; ++i) {
                        marketDataArray[i].processTick(tickEvent, barUpdateInfo, 3);
                        marketDataArray[i].processTick(tickEvent, barUpdateInfo, 2);
                    }
                    versatileData.reset();
                    continue;
                }
                iTickSimulator.init(versatileData);
                boolean bl = false;
                while (iTickSimulator.getNextTick(tickEvent)) {
                    if (!bl) {
                        session.checkTimeIsInSession(tickEvent.getTime(), sessionStatus, null);
                        bl = true;
                    }
                    tickEvent.setSessionStartTime(sessionStatus.sessionStartTime);
                    tickEvent.setSessionEndTime(sessionStatus.sessionEndTime);
                    barUpdateInfo.updatedChart = -1;
                    barUpdateInfo.multipleChartsUpdated = false;
                    barUpdateInfo.eventType = 1;
                    for (int i = 0; i < backtestTradingSetupArray.length; ++i) {
                        marketDataArray[i].processTick(tickEvent, barUpdateInfo, 3);
                        marketDataArray[i].processTick(tickEvent, barUpdateInfo, 2);
                    }
                    versatileData.reset();
                }
            }
            long l2 = System.currentTimeMillis();
            if (loadDataProgressEngine != null) {
                double d = (double)(l2 - l) / 1000.0;
                loadDataProgressEngine.printToLog(L.t((String)"Precomputed MarketData in %.4f s.", (Object[])new Object[]{d}));
            }
        }
        finally {
            iLoadedDataHolder.afterProduce();
        }
        return marketDataArray;
    }

    private HashPair[] computeHashPairs(ArrayList<ChartDef> arrayList) {
        ArrayList<Object> arrayList2 = new ArrayList<Object>();
        for (ChartDef chartDef : arrayList) {
            HashPair hashPair = new HashPair(chartDef.getConnectionHash(), chartDef.getSymbolHash());
            boolean bl = false;
            for (HashPair hashPair2 : arrayList2) {
                if (hashPair2.symbolHash != hashPair.symbolHash || hashPair2.connectionHash != hashPair.connectionHash) continue;
                bl = true;
                break;
            }
            if (bl) continue;
            arrayList2.add(hashPair);
        }
        HashPair[] hashPairArray = new HashPair[arrayList2.size()];
        int n = 0;
        for (HashPair hashPair : arrayList2) {
            hashPairArray[n++] = hashPair;
        }
        return hashPairArray;
    }

    public void destroy() {
        this.loadedDataHolder.afterProduce();
    }

    public void trackUsed() {
        ++this.usedCounter;
        this.lastTimeUsed = System.currentTimeMillis();
    }

    public void ensureDataType(int n) throws Exception {
        this.checkDataType(this.dataType, n);
    }

    private void checkDataType(int n, int n2) throws Exception {
        if (n == n2) {
            return;
        }
    }

    public MarketData[] getMarketData() {
        return this.loadedDataHolder.getMarketData();
    }

    public long freeIfInMemory() {
        return this.loadedDataHolder.freeIfInMemory();
    }

    public boolean isJustCreated() {
        return this.justCreated;
    }

    public void setNotJustCreated() {
        this.justCreated = false;
    }

    public Exception getException() {
        return this.loadException;
    }
}

