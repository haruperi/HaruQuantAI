/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.additional;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.lib.L;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.AdditionalDataFile;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.AdditionalDataLoader;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.LoadedAdditionalData;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AdditionalDataCache {
    public static final Logger Log = LoggerFactory.getLogger(AdditionalDataCache.class);
    private ILastEventListener lastEventListener;
    private static AdditionalDataCache instance;
    private ConcurrentHashMap<Integer, LoadedAdditionalData> mapCache = new ConcurrentHashMap();
    private AdditionalDataFile addditionalDataFile = new AdditionalDataFile();
    private IBacktestProgressListener backtestProgressListener;

    public static synchronized AdditionalDataCache getInstance() {
        if (instance == null) {
            instance = new AdditionalDataCache();
        }
        return instance;
    }

    public LoadedAdditionalData loadData(ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(L.t((String)"Loading additional data...", (Object[])new Object[0]));
        }
        int n = this.computeHash(chartSetup, pickerDataTimeline);
        LoadedAdditionalData loadedAdditionalData = null;
        try {
            loadedAdditionalData = this._loadData(n, chartSetup, pickerDataTimeline, stopPauseEngine);
        }
        catch (TaskStoppedException taskStoppedException) {
            Log.info("Loading data stopped");
            this.mapCache.remove(n);
            throw taskStoppedException;
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Exception when loading additional data - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        return loadedAdditionalData;
    }

    private LoadedAdditionalData _loadData(int n, ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        LoadedAdditionalData loadedAdditionalData = this.mapCache.computeIfAbsent(n, n2 -> this.createLoadedData(n, chartSetup, pickerDataTimeline, stopPauseEngine));
        if (loadedAdditionalData == null) {
            this.mapCache.remove(n);
            throw new Exception(L.t((String)"Loaded additional data is null", (Object[])new Object[0]));
        }
        if (loadedAdditionalData.getException() != null) {
            this.mapCache.remove(n);
            throw loadedAdditionalData.getException();
        }
        return loadedAdditionalData;
    }

    private LoadedAdditionalData createLoadedData(int n, ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) {
        LoadedAdditionalData loadedAdditionalData = null;
        try {
            Log.info("Loading additional data from file...");
            if (this.lastEventListener != null) {
                this.lastEventListener.setLastEvent(L.t((String)"Loading additional data from file...", (Object[])new Object[0]));
            }
            loadedAdditionalData = this.createDataFile(n, chartSetup, pickerDataTimeline, stopPauseEngine);
        }
        catch (Exception exception) {
            loadedAdditionalData = new LoadedAdditionalData();
            loadedAdditionalData.setException(exception);
        }
        return loadedAdditionalData;
    }

    private LoadedAdditionalData createDataFile(int n, ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        long l = System.currentTimeMillis();
        AdditionalDataLoader additionalDataLoader = new AdditionalDataLoader(chartSetup, pickerDataTimeline, this.lastEventListener, this.backtestProgressListener, stopPauseEngine);
        LoadedAdditionalData loadedAdditionalData = additionalDataLoader.load();
        return loadedAdditionalData;
    }

    private int computeHash(ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline) {
        int n;
        long l = System.currentTimeMillis();
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(pickerDataTimeline.hashCode());
        for (n = 1; n < chartSetup.getCharts().size(); ++n) {
            ChartDef chartDef = chartSetup.getCharts().get(n);
            stringBuilder.append(chartDef.getSymbol());
            stringBuilder.append(chartDef.getTimeframe());
        }
        n = stringBuilder.toString().hashCode();
        long l2 = System.currentTimeMillis() - l;
        Log.debug(String.format("Calculating hash of addditional data took " + l2 + "ms", new Object[0]));
        return n;
    }

    private String getFileNameByHash(int n) {
        return MainApp.getDataPath() + "internal/testfiles/picker/" + n;
    }

    public void setLastEventListener(ILastEventListener iLastEventListener) {
        this.lastEventListener = iLastEventListener;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }
}

