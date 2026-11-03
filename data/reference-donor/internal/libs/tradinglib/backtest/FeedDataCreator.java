/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.datalib.session.Session
 *  com.strategyquant.datalib.session.SessionManager
 *  com.strategyquant.datalib.session.SessionStatus
 *  com.strategyquant.lib.IStopPauseStatus
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TaskStoppedException
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.datalib.session.Session;
import com.strategyquant.datalib.session.SessionManager;
import com.strategyquant.datalib.session.SessionStatus;
import com.strategyquant.lib.IStopPauseStatus;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.backtest.DataLoadStats;
import com.strategyquant.tradinglib.backtest.IFeedDataSaver;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class FeedDataCreator {
    public static final Logger Log = LoggerFactory.getLogger((String)"FeedDataCreator");

    public void loadFeed(ArrayList<ChartDef> arrayList, int n, DataLoadStats dataLoadStats, IFeedDataSaver iFeedDataSaver, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        IDataLoader[] iDataLoaderArray = this.initializeDataLoaders(arrayList, n, loadDataProgressEngine);
        String string = arrayList.get(0).getSession();
        Int2ObjectOpenHashMap<ChartDef> int2ObjectOpenHashMap = this.createChartDefsMap(arrayList);
        Session session = SessionManager.getSession((String)string).clone();
        SessionStatus sessionStatus = new SessionStatus();
        long l = System.currentTimeMillis();
        VersatileData versatileData = new VersatileData();
        int n2 = 0;
        long l2 = -1L;
        int n3 = -1;
        long l3 = 0L;
        long l4 = 0L;
        if (loadDataProgressEngine != null) {
            loadDataProgressEngine.printToLog(L.t((String)"Creating backtest data feed", (Object[])new Object[0]) + "...");
        }
        Log.debug("DataLoaders: " + iDataLoaderArray.length);
        int n4 = iDataLoaderArray.length;
        Log.debug("FEED DATA CREATOR START");
        while (true) {
            Object object;
            if (loadDataProgressEngine != null && loadDataProgressEngine.getProgressEngine().isStopped()) {
                loadDataProgressEngine.printToLog(L.t((String)"Backtest data feed creation stopped", (Object[])new Object[0]));
                double d = (double)(System.currentTimeMillis() - l) / 1000.0;
                loadDataProgressEngine.onDataPreparationFinished(d, n2);
                for (IDataLoader iDataLoader : iDataLoaderArray) {
                    iDataLoader.close();
                }
                throw new TaskStoppedException();
            }
            l2 = -1L;
            n3 = -1;
            for (int i = 0; i < n4; ++i) {
                ++n2;
                object = iDataLoaderArray[i];
                if (!object.hasNextTick() || l2 != -1L && object.nextTickTime() >= l2) continue;
                n3 = i;
                l2 = object.nextTickTime();
            }
            if (n3 < 0) break;
            iDataLoaderArray[n3].getNextTick(versatileData);
            ChartDef chartDef = (ChartDef)int2ObjectOpenHashMap.get(versatileData.symbolHash);
            if (chartDef != null && (((String)(object = chartDef.getTimeframe())).equals("D1") || ((String)object).equals("Weekly") || ((String)object).equals("Monthly"))) {
                session.fixD1DataTime(versatileData);
            }
            session.checkTimeIsInSession(versatileData.time, sessionStatus, chartDef.getTimeframe());
            if (!sessionStatus.isInSession) continue;
            boolean bl = iDataLoaderArray[n3].isOHLCData();
            int n5 = iDataLoaderArray[n3].getDecimalPlaces();
            if (sessionStatus.sessionStartTime == Long.MIN_VALUE) {
                sessionStatus.sessionStartTime = SQTime.correctDayStart((long)versatileData.time);
            }
            versatileData.sessionStartTime = sessionStatus.sessionStartTime;
            iFeedDataSaver.setParams(bl, n5);
            iFeedDataSaver.saveTick(versatileData);
            if (l3 == 0L) {
                l3 = versatileData.time;
            }
            l4 = versatileData.time;
        }
        for (IDataLoader iDataLoader : iDataLoaderArray) {
            iDataLoader.close();
        }
        long l5 = System.currentTimeMillis();
        if (Log.isDebugEnabled()) {
            Log.debug("Loading backtest data FEED TOOK: " + (l5 - l) + " ms, ticks: " + n2);
            Log.debug("Very first tick time: " + SQTime.toDateMinuteString((long)l3));
            Log.debug("Very last tick time: " + SQTime.toDateMinuteString((long)l4));
        }
        if (loadDataProgressEngine != null) {
            double d = (double)(l5 - l) / 1000.0;
            loadDataProgressEngine.printToLog(L.t((String)"Created in %.4f s., ticks: %d", (Object[])new Object[]{d, n2}));
            loadDataProgressEngine.onDataPreparationFinished(d, n2);
        }
        dataLoadStats.loadingTime = l5 - l;
        dataLoadStats.ticks = n2;
    }

    private Int2ObjectOpenHashMap<ChartDef> createChartDefsMap(ArrayList<ChartDef> arrayList) throws DataException {
        Int2ObjectOpenHashMap int2ObjectOpenHashMap = new Int2ObjectOpenHashMap();
        for (ChartDef chartDef : arrayList) {
            ChartDef chartDef2;
            int n = chartDef.getSymbolHash();
            if (int2ObjectOpenHashMap.containsKey(n) && (chartDef2 = (ChartDef)int2ObjectOpenHashMap.get(n)).isSmallerThan(chartDef)) continue;
            int2ObjectOpenHashMap.put(n, (Object)chartDef);
        }
        return int2ObjectOpenHashMap;
    }

    public IDataLoader[] initializeDataLoaders(ArrayList<ChartDef> arrayList, int n, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        ArrayList<IDataLoader> arrayList2 = this.getUniqueChartDefs(arrayList, n, loadDataProgressEngine);
        IDataLoader[] iDataLoaderArray = new IDataLoader[arrayList2.size()];
        for (int i = 0; i < iDataLoaderArray.length; ++i) {
            iDataLoaderArray[i] = arrayList2.get(i);
        }
        return iDataLoaderArray;
    }

    private ArrayList<IDataLoader> getUniqueChartDefs(ArrayList<ChartDef> arrayList, int n, LoadDataProgressEngine loadDataProgressEngine) throws Exception {
        ArrayList<IDataLoader> arrayList2 = new ArrayList<IDataLoader>();
        for (int i = 0; i < arrayList.size(); ++i) {
            ChartDef chartDef = arrayList.get(i);
            boolean bl = true;
            for (int j = 0; j < arrayList.size(); ++j) {
                if (i == j) continue;
                ChartDef chartDef2 = arrayList.get(j);
                if (n == 1) {
                    if (!chartDef.canBeComputedFrom(chartDef2)) continue;
                    bl = false;
                    chartDef2.setLoadedHistoryFrom(Math.min(chartDef2.getLoadedHistoryFrom(), chartDef.getLoadedHistoryFrom()));
                    chartDef2.setHistoryTo(Math.max(chartDef2.getHistoryTo(), chartDef.getHistoryTo()));
                    continue;
                }
                if (j <= i || !chartDef.isSameConnectionSymbol(chartDef2)) continue;
                bl = false;
                chartDef2.setLoadedHistoryFrom(Math.min(chartDef2.getLoadedHistoryFrom(), chartDef.getLoadedHistoryFrom()));
                chartDef2.setHistoryTo(Math.max(chartDef2.getHistoryTo(), chartDef.getHistoryTo()));
            }
            if (!bl) continue;
            IDataLoader iDataLoader = DataManager.getDataLoader((ChartDef)chartDef, (int)n, (IStopPauseStatus)(loadDataProgressEngine != null ? loadDataProgressEngine.getProgressEngine() : null));
            iDataLoader.open();
            if (chartDef.getHistoryTo() < iDataLoader.getDateFrom()) {
                for (IDataLoader iDataLoader2 : arrayList2) {
                    iDataLoader2.close();
                }
                throw new DataException(2, "Date range for " + chartDef.getConnectionName() + " / " + chartDef.getSymbol() + " is incorrect! Requested range: " + SQTime.toDateString((long)chartDef.getHistoryFrom()) + "- " + SQTime.toDateString((long)chartDef.getHistoryTo()) + ", but the data start on " + SQTime.toDateString((long)iDataLoader.getDateFrom()));
            }
            arrayList2.add(iDataLoader);
        }
        return arrayList2;
    }
}

