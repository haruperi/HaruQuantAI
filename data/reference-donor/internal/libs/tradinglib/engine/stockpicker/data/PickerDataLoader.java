/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.lib.app.MainApp
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.LoadedPickerData;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.AdditionalDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupsDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupsDataLoader;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.DefaultTimeline;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataLoader {
    public static final Logger Log = LoggerFactory.getLogger(StockGroupsDataLoader.class);
    private ChartSetup chartSetup;
    private BasketDto dto;
    private ILastEventListener lastEventListener;
    private IBacktestProgressListener backtestProgressListener;
    private StopPauseEngine stopPauseEngine;

    public PickerDataLoader(ChartSetup chartSetup, BasketDto basketDto, ILastEventListener iLastEventListener, IBacktestProgressListener iBacktestProgressListener, StopPauseEngine stopPauseEngine) {
        this.chartSetup = chartSetup;
        this.dto = basketDto;
        this.lastEventListener = iLastEventListener;
        this.backtestProgressListener = iBacktestProgressListener;
        this.stopPauseEngine = stopPauseEngine;
    }

    public LoadedPickerData load() throws Exception {
        PickerDataTimeline pickerDataTimeline;
        long l = System.currentTimeMillis();
        LoadedPickerData loadedPickerData = new LoadedPickerData();
        if (this.useDefaultTimeline(this.dto)) {
            Log.info(String.format("Default timeline will be used while loading %s data...", this.dto.getName()));
            pickerDataTimeline = DefaultTimeline.getInstance();
        } else {
            pickerDataTimeline = new PickerDataTimeline();
            pickerDataTimeline.init(this.dto, this.stopPauseEngine);
        }
        loadedPickerData.timeline = pickerDataTimeline;
        StockGroupsDataCache stockGroupsDataCache = StockGroupsDataCache.getInstance();
        stockGroupsDataCache.setLastEventListener(this.lastEventListener);
        stockGroupsDataCache.registerProgressListener(this.backtestProgressListener);
        loadedPickerData.stockGroupData = stockGroupsDataCache.loadData(this.chartSetup, this.dto, pickerDataTimeline, this.stopPauseEngine);
        AdditionalDataCache additionalDataCache = AdditionalDataCache.getInstance();
        additionalDataCache.setLastEventListener(this.lastEventListener);
        additionalDataCache.registerProgressListener(this.backtestProgressListener);
        loadedPickerData.additionalData = additionalDataCache.loadData(this.chartSetup, pickerDataTimeline, this.stopPauseEngine);
        long l2 = System.currentTimeMillis() - l;
        String string = SQTimeOld.formatDateTime((long)((int)(l2 / 1000L)));
        Log.info("Loading {} data done in {}", (Object)this.dto.getName(), (Object)string);
        return loadedPickerData;
    }

    private boolean useDefaultTimeline(BasketDto basketDto) {
        return MainApp.getProduct() == "BACKTESTNODE" && basketDto.getName().startsWith("[[") && DefaultTimeline.getInstance().generated;
    }
}

