/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.basket.BasketDto
 *  com.strategyquant.datalib.basket.BasketOfStocksManager
 *  com.strategyquant.datalib.basket.StockDto
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.JobDetails
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.app.MainApp
 *  it.unimi.dsi.fastutil.objects.ObjectOpenHashSet
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data;

import com.strategyquant.datalib.basket.BasketDto;
import com.strategyquant.datalib.basket.BasketOfStocksManager;
import com.strategyquant.datalib.basket.StockDto;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.JobDetails;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.app.MainApp;
import com.strategyquant.tradinglib.engine.stockpicker.data.PickerDataPreloaderJob;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.DefaultTimeline;
import com.strategyquant.tradinglib.engine.stockpicker.data.timeline.PickerDataTimeline;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.simplegrid.SimpleGridEngine;
import it.unimi.dsi.fastutil.objects.ObjectOpenHashSet;
import java.io.File;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PickerDataPreloader {
    public static final Logger Log = LoggerFactory.getLogger(PickerDataPreloader.class);
    protected static final String connectionName = "History";
    private int lastIndex;
    private long total;
    protected ConcurrentHashMap<String, String> symbolsMissing = new ConcurrentHashMap();
    public Set<String> uniqueSymbols = Collections.synchronizedSet(new ObjectOpenHashSet());
    public Set<String> loadedSymbols = Collections.synchronizedSet(new ObjectOpenHashSet());

    public int total() {
        return this.uniqueSymbols.size();
    }

    public int loaded() {
        return this.loadedSymbols.size();
    }

    public void clearStats() {
        this.symbolsMissing.clear();
        this.uniqueSymbols.clear();
        this.loadedSymbols.clear();
    }

    public void load() throws Exception {
        DataManager.get().refreshDataInfoCache();
        DefaultTimeline defaultTimeline = DefaultTimeline.getInstance();
        defaultTimeline.generate();
        this.loadSymbolData(defaultTimeline);
    }

    public void loadSymbolData(PickerDataTimeline pickerDataTimeline) throws Exception {
        List list = BasketOfStocksManager.getInstance().getGroups();
        for (int i = 0; i < list.size(); ++i) {
            BasketDto basketDto = (BasketDto)list.get(i);
            if (basketDto.getName().equalsIgnoreCase("[[S&P 100 limited]]") || !basketDto.isDefault()) continue;
            this.runOnGrid(basketDto, pickerDataTimeline);
        }
        this.writeMissingSymbolsToFile();
    }

    private void runOnGrid(final BasketDto basketDto, final PickerDataTimeline pickerDataTimeline) throws Exception {
        final List list = BasketOfStocksManager.getInstance().getStocks(basketDto.getId().intValue());
        this.total = list.size();
        this.lastIndex = 0;
        Log.info(String.format("Preloading %d symbols data of group %s.", this.total, basketDto.getName()));
        SimpleGridEngine<PickerDataPreloaderJob, String> simpleGridEngine = new SimpleGridEngine<PickerDataPreloaderJob, String>(this, new StopPauseEngine(), null, false){
            final /* synthetic */ PickerDataPreloader this$0;
            {
                this.this$0 = pickerDataPreloader;
                super(stopPauseEngine, gridJob, bl);
            }

            @Override
            protected ArrayList<PickerDataPreloaderJob> createJobsBatch(int n, GridClient gridClient) throws Exception {
                return this.this$0.createBatch(n, basketDto, list, pickerDataTimeline);
            }

            @Override
            protected void processResult(String string, JobDetails jobDetails) throws Exception {
                if (string == null) {
                    return;
                }
                this.this$0.loadedSymbols.add(string);
            }

            @Override
            protected void onError(String string, Exception exception) {
                Log.error("Data loader Error {}, Exception ", (Object)string, (Object)exception);
            }
        };
        simpleGridEngine.start();
        simpleGridEngine.unregisterListeners();
    }

    protected ArrayList<PickerDataPreloaderJob> createBatch(int n, BasketDto basketDto, List<StockDto> list, PickerDataTimeline pickerDataTimeline) throws Exception {
        ArrayList<PickerDataPreloaderJob> arrayList = new ArrayList<PickerDataPreloaderJob>();
        int n2 = 0;
        while ((long)this.lastIndex < this.total && n2 != n) {
            StockDto stockDto = list.get(this.lastIndex);
            String string = stockDto.getTicker();
            if (!this.uniqueSymbols.contains(string)) {
                this.uniqueSymbols.add(string);
                PickerDataPreloaderJob pickerDataPreloaderJob = new PickerDataPreloaderJob(string, string + this.lastIndex + basketDto.getName(), basketDto, pickerDataTimeline, this.symbolsMissing);
                arrayList.add(pickerDataPreloaderJob);
                ++n2;
            }
            ++this.lastIndex;
        }
        if (arrayList.size() == 0) {
            return null;
        }
        return arrayList;
    }

    private void writeMissingSymbolsToFile() {
        File file = new File(MainApp.getDataPath() + "picker_symbols_missing.txt");
        if (file.exists()) {
            file.delete();
        }
        StringBuilder stringBuilder = new StringBuilder();
        for (Map.Entry<String, String> entry : this.symbolsMissing.entrySet()) {
            stringBuilder.append(entry.getKey() + "," + entry.getValue() + "\n");
        }
        SQUtils.stringToFile((File)file, (String)stringBuilder.toString());
    }
}

