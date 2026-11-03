/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.SymbolsDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.HashMap;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataPreloaderJob
extends GridJob<String> {
    public static final Logger Log = LoggerFactory.getLogger(PickerDataPreloaderJob.class);
    private String symbol;
    private BasketDto gi;
    private PickerDataTimeline timeline;
    private ConcurrentHashMap<String, String> symbolsMissing;

    public PickerDataPreloaderJob(String string, String string2, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, ConcurrentHashMap<String, String> concurrentHashMap) {
        super(string2, 1, new HashMap());
        this.symbol = string;
        this.gi = basketDto;
        this.timeline = pickerDataTimeline;
        this.symbolsMissing = concurrentHashMap;
    }

    public String call() throws Exception {
        try {
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.symbol, (boolean)true);
            if (dataInfo == null) {
                throw new Exception(L.t((String)"Data for symbol '%s' cannot be found!", (Object[])new Object[]{this.symbol}));
            }
            Log.debug(String.format("Data found %s/%s, from %s to %s.", this.symbol, this.gi.getName(), SQTime.toDateString((long)dataInfo.dateFrom), SQTime.toDateString((long)dataInfo.dateTo)));
            if (dataInfo.rows < 1) {
                throw new Exception(L.t((String)"No data available for symbol '%s'", (Object[])new Object[]{this.symbol}));
            }
            SymbolsDataCache symbolsDataCache = SymbolsDataCache.getInstance();
            symbolsDataCache.loadData(dataInfo, this.timeline, new StopPauseEngine());
            return this.symbol;
        }
        catch (Exception exception) {
            this.symbolsMissing.put(this.symbol, this.gi.getName() + "," + exception.getMessage());
            Log.info(String.format("Couldn't load symbol data %s/%s. Reason: %s", this.symbol, this.gi.getName(), exception.getMessage()));
            return null;
        }
    }
}

