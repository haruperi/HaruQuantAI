/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.DataManager
 *  com.strategyquant.datalib.data.io.IDataLoader
 *  com.strategyquant.datalib.data.io.VersatileData
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.lib.TaskStoppedException
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine.stockpicker.data.timeline;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.datalib.data.io.IDataLoader;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.SQTime;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.engine.stockpicker.backtester.PortfolioBacktestJob;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.HashMap;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TimelineCalcJob
extends GridJob<String> {
    public static final Logger Log = LoggerFactory.getLogger(PortfolioBacktestJob.class);
    private String symbol;
    private Set<Long> timeline;
    private StopPauseEngine stopPauseEngine;

    public TimelineCalcJob(String string, String string2, Set<Long> set, StopPauseEngine stopPauseEngine) {
        super(string2, 1, new HashMap());
        this.symbol = string;
        this.timeline = set;
        this.stopPauseEngine = stopPauseEngine;
    }

    public String call() throws Exception {
        try {
            DataInfo dataInfo = DataManager.getDataInfo((String)"History", (String)this.symbol, (boolean)true);
            if (dataInfo == null || dataInfo.rows < 1) {
                return null;
            }
            this.loadSymbolData(dataInfo);
        }
        catch (Exception exception) {
            Log.info(String.format("Couldn't load %s data. Reason: %s", this.symbol, exception.getMessage()), (Throwable)exception);
        }
        return null;
    }

    private void loadSymbolData(DataInfo dataInfo) throws Exception {
        try (IDataLoader iDataLoader = null;){
            iDataLoader = DataManager.getDataLoader((ChartDef)new ChartDef("History", dataInfo.symbol, "D1", dataInfo.dateFrom, dataInfo.dateTo, dataInfo.symbolInfo.defaultSpread, "No Session"), (int)1);
            iDataLoader.open();
            VersatileData versatileData = new VersatileData();
            while (iDataLoader.hasNextTick()) {
                if (this.stopPauseEngine.isStopped()) {
                    throw new TaskStoppedException();
                }
                iDataLoader.getNextTick(versatileData);
                long l = SQTime.getDateInMs((long)versatileData.time);
                this.timeline.add(l);
            }
            iDataLoader.close();
        }
    }
}

