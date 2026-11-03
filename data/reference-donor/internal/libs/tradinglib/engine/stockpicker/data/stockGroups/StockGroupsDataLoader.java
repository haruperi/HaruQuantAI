/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.TaskStoppedException
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.LoadedStockGroupData;
import com.strategyquant.tradinglib.engine.stockpicker.data.stockGroups.StockGroupDataLoaderJob;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import java.util.ArrayList;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StockGroupsDataLoader {
    public static final Logger Log = LoggerFactory.getLogger(StockGroupsDataLoader.class);
    private ChartSetup chartSetup;
    private BasketDto dto;
    private ILastEventListener lastEventListener;
    private IBacktestProgressListener backtestProgressListener;
    private StopPauseEngine stopPauseEngine;
    private double total;
    private double processed = 0.0;
    private int progress = 1;
    private int lastProgress = 0;
    private int lastIndex;
    private PickerDataTimeline timeline;

    public StockGroupsDataLoader(ChartSetup chartSetup, BasketDto basketDto, PickerDataTimeline pickerDataTimeline, ILastEventListener iLastEventListener, IBacktestProgressListener iBacktestProgressListener, StopPauseEngine stopPauseEngine) {
        this.chartSetup = chartSetup;
        this.dto = basketDto;
        this.timeline = pickerDataTimeline;
        this.lastEventListener = iLastEventListener;
        this.backtestProgressListener = iBacktestProgressListener;
        this.stopPauseEngine = stopPauseEngine;
    }

    public LoadedStockGroupData load() throws Exception {
        long l = System.currentTimeMillis();
        LoadedStockGroupData loadedStockGroupData = new LoadedStockGroupData(this.dto);
        this.runOnGrid(loadedStockGroupData);
        long l2 = System.currentTimeMillis() - l;
        String string = SQTimeOld.formatDateTime((long)((int)(l2 / 1000L)));
        Log.info("Loading {} data done in {}", (Object)this.dto.getName(), (Object)string);
        return loadedStockGroupData;
    }

    private void runOnGrid(final LoadedStockGroupData loadedStockGroupData) throws Exception {
        this.lastIndex = 0;
        this.processed = 0.0;
        final List list = BasketOfStocksManager.getInstance().getStocks(this.dto.getId().intValue());
        this.total = list.size();
        SimpleGridEngine<StockGroupDataLoaderJob, String> simpleGridEngine = new SimpleGridEngine<StockGroupDataLoaderJob, String>(this, this.stopPauseEngine, null, false){
            final /* synthetic */ StockGroupsDataLoader this$0;
            {
                this.this$0 = stockGroupsDataLoader;
                super(stopPauseEngine, gridJob, bl);
            }

            @Override
            protected ArrayList<StockGroupDataLoaderJob> createJobsBatch(int n, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(n, loadedStockGroupData, list);
            }

            @Override
            protected void processResult(String string, JobDetails jobDetails) throws Exception {
                StockGroupsDataLoader.access$008(this.this$0);
                this.this$0.progress = (int)(this.this$0.processed / this.this$0.total / 4.0 * 100.0);
                Log.debug("Loaded symbols {}/{}", (Object)this.this$0.processed, (Object)this.this$0.total);
                if (this.this$0.backtestProgressListener != null && this.this$0.progress != this.this$0.lastProgress && (double)this.this$0.progress % 5.0 == 0.0) {
                    this.this$0.backtestProgressListener.setProgress(this.this$0.progress);
                    this.this$0.lastProgress = this.this$0.progress;
                }
            }

            @Override
            protected void onError(String string, Exception exception) {
                Log.error("Stock groups loader Error {}, Exception ", (Object)string, (Object)exception);
            }
        };
        simpleGridEngine.start();
        simpleGridEngine.unregisterListeners();
    }

    protected ArrayList<StockGroupDataLoaderJob> createBatch(int n, LoadedStockGroupData loadedStockGroupData, List<StockDto> list) throws Exception {
        ArrayList<StockGroupDataLoaderJob> arrayList = new ArrayList<StockGroupDataLoaderJob>();
        int n2 = 0;
        for (int i = this.lastIndex; i < this.lastIndex + n && !((double)i >= this.total); ++i) {
            if (this.stopPauseEngine.isStopped()) {
                throw new TaskStoppedException();
            }
            StockDto stockDto = list.get(i);
            StockGroupDataLoaderJob stockGroupDataLoaderJob = new StockGroupDataLoaderJob(stockDto.getTicker(), stockDto.getTicker() + i, loadedStockGroupData, this.timeline, this.stopPauseEngine, this.lastEventListener);
            arrayList.add(stockGroupDataLoaderJob);
            ++n2;
        }
        this.lastIndex += n2;
        if (arrayList.size() == 0) {
            return null;
        }
        return arrayList;
    }

    static /* synthetic */ double access$008(StockGroupsDataLoader stockGroupsDataLoader) {
        double d = stockGroupsDataLoader.processed;
        stockGroupsDataLoader.processed = d + 1.0;
        return d;
    }
}

