/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.SymbolsDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.HashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockGroupDataLoaderJob
extends GridJob<String> {
    public static final Logger Log = LoggerFactory.getLogger(StockGroupDataLoaderJob.class);
    private String symbol;
    private StockDto stockInfo;
    private ChartDef chartDef;
    private LoadedStockGroupData stockGroupData;
    private PickerDataTimeline timeline;
    private StopPauseEngine stopPauseEngine;
    private ILastEventListener lastEventListener;

    public StockGroupDataLoaderJob(String string, String string2, LoadedStockGroupData loadedStockGroupData, PickerDataTimeline pickerDataTimeline, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener) {
        super(string2, 1, new HashMap());
        this.symbol = string;
        this.stockGroupData = loadedStockGroupData;
        this.timeline = pickerDataTimeline;
        this.stopPauseEngine = stopPauseEngine;
        this.lastEventListener = iLastEventListener;
    }

    public String call() throws Exception {
        try {
            DataInfo dataInfo;
            if (Stockpicker.isDebugModeEnabled()) {
                Log.debug(String.format("Loading data %s...", this.symbol));
            }
            if (this.lastEventListener != null) {
                this.lastEventListener.setLastEvent(L.t((String)"Loading data %s...", (Object[])new Object[]{this.symbol}));
            }
            if ((dataInfo = DataManager.getDataInfo((String)"History", (String)this.symbol, (boolean)true)) == null) {
                Log.debug("Data for symbol '" + this.symbol + "' cannot be found!");
                return null;
            }
            this.symbol = dataInfo.symbol;
            if (dataInfo.rows < 1) {
                Log.debug("No data available for symbol '" + this.symbol + "'");
                return null;
            }
            SymbolsDataCache symbolsDataCache = SymbolsDataCache.getInstance();
            symbolsDataCache.setLastEventListener(this.lastEventListener);
            LoadedSymbolData loadedSymbolData = symbolsDataCache.loadData(dataInfo, this.timeline, this.stopPauseEngine);
            this.stockGroupData.putSymbolData(this.symbol, loadedSymbolData);
        }
        catch (Exception exception) {
            Log.info(String.format("Couldn't load %s data. Reason: %s", this.symbol, exception.getMessage()), (Throwable)exception);
        }
        return null;
    }
}

