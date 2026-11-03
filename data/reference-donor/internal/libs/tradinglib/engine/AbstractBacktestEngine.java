/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtestrunner.IBacktestProgressListener;
import com.strategyquant.tradinglib.engine.BacktestEngine;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.robustnesstests.DataModifierCallback;

public abstract class AbstractBacktestEngine {
    protected boolean singleThreaded = true;
    protected DataModifierCallback dataModifierCallback;
    protected StopPauseEngine stopPauseEngine;
    protected IBacktestProgressListener backtestProgressListener;
    protected LoadDataProgressEngine loadDataProgressEngine = null;
    protected String lastSettingsXml = null;
    protected boolean usePreparedData = true;
    protected double globalATR;

    public void setSingleThreaded(boolean bl) {
        this.singleThreaded = bl;
    }

    public void setDataModifierCallback(DataModifierCallback dataModifierCallback) {
        this.dataModifierCallback = dataModifierCallback;
    }

    public void setStopPauseEngine(StopPauseEngine stopPauseEngine) {
        this.stopPauseEngine = stopPauseEngine;
    }

    public void registerProgressListener(IBacktestProgressListener iBacktestProgressListener) {
        this.backtestProgressListener = iBacktestProgressListener;
    }

    public void setLoadDataProgressEngine(LoadDataProgressEngine loadDataProgressEngine) {
        this.loadDataProgressEngine = loadDataProgressEngine;
    }

    public void setLastSettings(String string) {
        this.lastSettingsXml = string;
    }

    public void setUsePreparedData(boolean bl) {
        this.usePreparedData = bl;
    }

    public abstract int getEngineId();

    public abstract BacktestEngine runBacktest() throws Exception;

    public abstract BacktestEngine runBacktest(String var1, String var2, boolean var3) throws Exception;

    public abstract void addSetup(SettingsMap var1) throws Exception;

    public abstract double getGlobalATR();
}

