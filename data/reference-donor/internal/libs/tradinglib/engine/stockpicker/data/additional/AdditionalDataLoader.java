/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.additional;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.lib.L;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.Stockpicker;
import com.strategyquant.tradinglib.engine.stockpicker.data.additional.LoadedAdditionalData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.LoadedSymbolData;
import com.strategyquant.tradinglib.engine.stockpicker.data.symbols.SymbolsDataCache;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AdditionalDataLoader {
    public static final Logger Log = LoggerFactory.getLogger(AdditionalDataLoader.class);
    private ChartSetup chartSetup;
    private ILastEventListener lastEventListener;
    private IBacktestProgressListener backtestProgressListener;
    private StopPauseEngine stopPauseEngine;
    private PickerDataTimeline timeline;
    private LoadedAdditionalData additionalData = new LoadedAdditionalData();

    public AdditionalDataLoader(ChartSetup chartSetup, PickerDataTimeline pickerDataTimeline, ILastEventListener iLastEventListener, IBacktestProgressListener iBacktestProgressListener, StopPauseEngine stopPauseEngine) {
        this.chartSetup = chartSetup;
        this.timeline = pickerDataTimeline;
        this.lastEventListener = iLastEventListener;
        this.backtestProgressListener = iBacktestProgressListener;
        this.stopPauseEngine = stopPauseEngine;
    }

    public LoadedAdditionalData load() throws Exception {
        Object object;
        long l = System.currentTimeMillis();
        String string = this.chartSetup.getMainChart().getSymbol();
        for (int i = 1; i < this.chartSetup.getCharts().size(); ++i) {
            String string2 = "NA";
            try {
                DataInfo dataInfo;
                object = this.chartSetup.getCharts().get(i);
                string2 = object.getSymbol();
                if (string.equals(string2)) {
                    this.additionalData.add(null);
                    continue;
                }
                if (Stockpicker.isDebugModeEnabled()) {
                    Log.debug(String.format("Loading additional data %d/%s...", i, string2));
                }
                if (this.lastEventListener != null) {
                    this.lastEventListener.setLastEvent(L.t((String)"Loading additional data %s...", (Object[])new Object[]{string2}));
                }
                if ((dataInfo = DataManager.getDataInfo((String)"History", (String)string2, (boolean)true)) == null) {
                    throw new Exception(L.t((String)"Data for symbol '%s' cannot be found!", (Object[])new Object[]{string2}));
                }
                string2 = dataInfo.symbol;
                if (dataInfo.rows < 1) {
                    throw new Exception(L.t((String)"No data available for symbol '%s'", (Object[])new Object[]{string2}));
                }
                SymbolsDataCache symbolsDataCache = SymbolsDataCache.getInstance();
                symbolsDataCache.setLastEventListener(this.lastEventListener);
                LoadedSymbolData loadedSymbolData = symbolsDataCache.loadData(dataInfo, this.timeline, this.stopPauseEngine);
                this.additionalData.add(loadedSymbolData);
                continue;
            }
            catch (Exception exception) {
                throw new Exception(L.t((String)"Error while loading additional data %d/%s - %s", (Object[])new Object[]{i, string2, exception.getMessage()}), exception);
            }
        }
        long l2 = System.currentTimeMillis() - l;
        object = SQTimeOld.formatDateTime((long)((int)(l2 / 1000L)));
        Log.info("Loading additional data done in {}", object);
        return this.additionalData;
    }
}

