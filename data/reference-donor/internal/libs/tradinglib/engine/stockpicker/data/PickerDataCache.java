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
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataLoader;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.List;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataCache {
    public static final Logger Log = LoggerFactory.getLogger(PickerDataCache.class);
    private static PickerDataCache instance;
    private ConcurrentHashMap<Integer, LoadedPickerData> mapCache = new ConcurrentHashMap();
    private IBacktestProgressListener backtestProgressListener;

    public static synchronized PickerDataCache getInstance() {
        if (instance == null) {
            instance = new PickerDataCache();
        }
        return instance;
    }

    public LoadedPickerData loadData(ChartSetup chartSetup, BasketDto basketDto, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener) throws Exception {
        int n = this.computeHash(basketDto, chartSetup);
        LoadedPickerData loadedPickerData = null;
        try {
            loadedPickerData = this._loadData(n, chartSetup, basketDto, stopPauseEngine, iLastEventListener);
        }
        catch (TaskStoppedException taskStoppedException) {
            Log.info("Loading data stopped");
            this.mapCache.remove(n);
            throw taskStoppedException;
        }
        catch (Exception exception) {
            throw new Exception(L.t((String)"Exception when loading picker data - %s", (Object[])new Object[]{exception.getMessage()}), exception);
        }
        return loadedPickerData;
    }

    private LoadedPickerData _loadData(int n, ChartSetup chartSetup, BasketDto basketDto, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener) throws Exception {
        LoadedPickerData loadedPickerData = this.mapCache.computeIfAbsent(n, n2 -> this.createLoadedData(n, chartSetup, basketDto, stopPauseEngine, iLastEventListener));
        if (loadedPickerData == null) {
            this.mapCache.remove(n);
            throw new Exception(L.t((String)"Loaded picker data is null", (Object[])new Object[0]));
        }
        if (loadedPickerData.getException() != null) {
            this.mapCache.remove(n);
            throw loadedPickerData.getException();
        }
        return loadedPickerData;
    }

    private LoadedPickerData createLoadedData(int n, ChartSetup chartSetup, BasketDto basketDto, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener) {
        LoadedPickerData loadedPickerData = null;
        try {
            Log.info(String.format("Loading %s data...", basketDto.getName()));
            if (iLastEventListener != null) {
                iLastEventListener.setLastEvent(String.format(L.t((String)"Loading %s data...", (Object[])new Object[]{basketDto.getName()}), new Object[0]));
            }
            PickerDataLoader pickerDataLoader = new PickerDataLoader(chartSetup, basketDto, iLastEventListener, this.backtestProgressListener, stopPauseEngine);
            loadedPickerData = pickerDataLoader.load();
        }
        catch (Exception exception) {
            loadedPickerData = new LoadedPickerData();
            loadedPickerData.setException(exception);
        }
        return loadedPickerData;
    }

    private int computeHash(BasketDto basketDto, ChartSetup chartSetup) {
        StockDto stockDto;
        int n;
        Log.debug(String.format("Calculating hash", new Object[0]));
        long l = System.currentTimeMillis();
        StringBuilder stringBuilder = new StringBuilder();
        stringBuilder.append(basketDto.getId());
        List list = BasketOfStocksManager.getInstance().getStocks(basketDto.getId().intValue());
        for (n = 0; n < list.size(); ++n) {
            stockDto = (StockDto)list.get(n);
            stringBuilder.append(stockDto.getTicker());
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)stockDto.getTicker(), (boolean)true);
            if (dataInfo == null || dataInfo.rows < 1) continue;
            stringBuilder.append(dataInfo.dateFrom);
            stringBuilder.append(dataInfo.dateTo);
        }
        for (n = 1; n < chartSetup.getCharts().size(); ++n) {
            stockDto = chartSetup.getCharts().get(n);
            stringBuilder.append(stockDto.getSymbol());
            stringBuilder.append(stockDto.getTimeframe());
        }
        n = stringBuilder.toString().hashCode();
        long l2 = System.currentTimeMillis() - l;
        Log.debug(String.format("Calculating hash of stock group data took " + l2 + "ms", new Object[0]));
        return n;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }
}

