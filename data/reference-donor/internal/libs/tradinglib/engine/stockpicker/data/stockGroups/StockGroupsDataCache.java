/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.app.MainApp
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupDataFile;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupsDataLoader;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockGroupsDataCache {
    public static final Logger Log = LoggerFactory.getLogger(StockGroupsDataCache.class);
    private ILastEventListener lastEventListener;
    private static StockGroupsDataCache instance;
    private ConcurrentHashMap<Integer, LoadedStockGroupData> mapCache = new ConcurrentHashMap();
    private StockGroupDataFile stockGroupFile = new StockGroupDataFile();
    private IBacktestProgressListener backtestProgressListener;

    public static synchronized StockGroupsDataCache getInstance() {
        if (instance == null) {
            instance = new StockGroupsDataCache();
        }
        return instance;
    }

    public LoadedStockGroupData loadData(ChartSetup chartSetup, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        if (this.lastEventListener != null) {
            this.lastEventListener.setLastEvent(L.t((String)"Loading stock group data...", (Object[])new Object[0]));
        }
        int n = this.computeHash(basketDto, pickerDataTimeline);
        LoadedStockGroupData loadedStockGroupData = null;
        try {
            loadedStockGroupData = this._loadData(n, chartSetup, basketDto, pickerDataTimeline, stopPauseEngine);
        }
        catch (TaskStoppedException taskStoppedException) {
            Log.info("Loading data stopped");
            this.mapCache.remove(n);
            throw taskStoppedException;
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Exception when loading stock group data - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        return loadedStockGroupData;
    }

    private LoadedStockGroupData _loadData(int n, ChartSetup chartSetup, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        LoadedStockGroupData loadedStockGroupData = this.mapCache.computeIfAbsent(n, n2 -> this.createLoadedData(n, chartSetup, basketDto, pickerDataTimeline, stopPauseEngine));
        if (loadedStockGroupData == null) {
            this.mapCache.remove(n);
            throw new Exception(L.t((String)"Loaded stock group data is null", (Object[])new Object[0]));
        }
        if (loadedStockGroupData.getException() != null) {
            this.mapCache.remove(n);
            throw loadedStockGroupData.getException();
        }
        return loadedStockGroupData;
    }

    private LoadedStockGroupData createLoadedData(int n, ChartSetup chartSetup, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) {
        LoadedStockGroupData loadedStockGroupData = null;
        try {
            Log.info(String.format("Loading %s data from db...", basketDto.getName()));
            if (this.lastEventListener != null) {
                this.lastEventListener.setLastEvent(String.format(L.t((String)"Loading %s data from db...", (Object[])new Object[0]), basketDto.getName()));
            }
            loadedStockGroupData = this.createDataFile(n, chartSetup, basketDto, pickerDataTimeline, stopPauseEngine);
        }
        catch (Exception exception) {
            loadedStockGroupData = new LoadedStockGroupData();
            loadedStockGroupData.setException(exception);
        }
        return loadedStockGroupData;
    }

    private LoadedStockGroupData createDataFile(int n, ChartSetup chartSetup, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine) throws Exception {
        long l = System.currentTimeMillis();
        StockGroupsDataLoader stockGroupsDataLoader = new StockGroupsDataLoader(chartSetup, basketDto, pickerDataTimeline, this.lastEventListener, this.backtestProgressListener, stopPauseEngine);
        LoadedStockGroupData loadedStockGroupData = stockGroupsDataLoader.load();
        return loadedStockGroupData;
    }

    private int computeHash(BasketDto basketDto, PickerDataTimeline pickerDataTimeline) {
        int n;
        long l = System.currentTimeMillis();
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(pickerDataTimeline.hashCode());
        stringBuilder.append(basketDto.getId());
        List list = BasketOfStocksManager.getInstance().getStocks(basketDto.getId().intValue());
        for (n = 0; n < list.size(); ++n) {
            StockDto stockDto = (StockDto)list.get(n);
            stringBuilder.append(stockDto.getTicker());
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)stockDto.getTicker(), (boolean)true);
            if (dataInfo == null || dataInfo.rows < 1) continue;
            stringBuilder.append(dataInfo.dateFrom);
            stringBuilder.append(dataInfo.dateTo);
        }
        n = stringBuilder.toString().hashCode();
        long l2 = System.currentTimeMillis() - l;
        Log.debug(String.format("Calculating hash of stock group data took " + l2 + "ms", new Object[0]));
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

