/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.TaskStoppedException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.symbols;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.lib.L;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.SymbolDataLoader;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SymbolsDataCache {
    public static final Logger Log = LoggerFactory.getLogger(SymbolsDataCache.class);
    private ILastEventListener lastEventListener;
    private static SymbolsDataCache instance;
    private ConcurrentHashMap<Integer, LoadedSymbolData> mapCache = new ConcurrentHashMap();
    private IBacktestProgressListener backtestProgressListener;

    public static synchronized SymbolsDataCache getInstance() {
        if (instance == null) {
            instance = new SymbolsDataCache();
        }
        return instance;
    }

    public LoadedSymbolData loadData(DataInfo dataInfo, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(L.t((String)"Loading symbol %s data ...", (Object[])new Object[]{dataInfo.symbol}));
        }
        int n = this.computeHash(dataInfo, pickerDataTimeline);
        LoadedSymbolData loadedSymbolData = null;
        try {
            loadedSymbolData = this._loadData(n, dataInfo, pickerDataTimeline, stopPauseEngine);
        }
        catch (TaskStoppedException taskStoppedException) {
            Log.info("Loading data stopped");
            this.mapCache.remove(n);
            throw taskStoppedException;
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Exception when loading symbol data - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        return loadedSymbolData;
    }

    private LoadedSymbolData _loadData(int n, DataInfo dataInfo, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        LoadedSymbolData loadedSymbolData = this.mapCache.computeIfAbsent(n, n2 -> this.createLoadedData(n, dataInfo, pickerDataTimeline, stopPauseEngine));
        if (loadedSymbolData == null) {
            this.mapCache.remove(n);
            throw new Exception(L.t((String)"Loaded picker data is null", (Object[])new Object[0]));
        }
        if (loadedSymbolData.getException() != null) {
            this.mapCache.remove(n);
            throw loadedSymbolData.getException();
        }
        return loadedSymbolData;
    }

    private LoadedSymbolData createLoadedData(int n, DataInfo dataInfo, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) {
        LoadedSymbolData loadedSymbolData = null;
        try {
            Log.debug(String.format("Loading symbol %s data from file...", dataInfo.symbol));
            if (this.lastEventListener != null) {
                this.lastEventListener.setLastEvent(L.t((String)"Loading symbol %s data from file...", (Object[])new Object[]{dataInfo.symbol}));
            }
            SymbolDataLoader symbolDataLoader = new SymbolDataLoader();
            loadedSymbolData = symbolDataLoader.load(dataInfo, pickerDataTimeline, stopPauseEngine);
        }
        catch (Exception exception) {
            loadedSymbolData = new LoadedSymbolData();
            loadedSymbolData.setException(exception);
        }
        return loadedSymbolData;
    }

    private int computeHash(DataInfo dataInfo, PickerDataTimeline pickerDataTimeline) {
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(pickerDataTimeline.hashCode());
        stringBuilder.append(dataInfo.symbol);
        stringBuilder.append(dataInfo.dateFrom);
        stringBuilder.append(dataInfo.dateTo);
        return stringBuilder.toString().hashCode();
    }

    public void setLastEventListener(ILastEventListener iLastEventListener) {
        this.lastEventListener = iLastEventListener;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }
}

