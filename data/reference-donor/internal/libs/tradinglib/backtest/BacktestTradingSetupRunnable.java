/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.data.IDataBuffer
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.data.IDataBuffer;
import com.strategyquant.tradinglib.engine.BacktestTradingSetup;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.setup.TradingSetupRunnable;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestTradingSetupRunnable
extends TradingSetupRunnable {
    public static final Logger Log = LoggerFactory.getLogger((String)"BacktestTradingSetupRunnable");

    public BacktestTradingSetupRunnable(BacktestTradingSetup backtestTradingSetup, IDataBuffer iDataBuffer, boolean bl) {
        super(backtestTradingSetup, bl);
    }

    @Override
    public void run() {
        boolean bl = true;
    }

    public void runCalled(TickEvent tickEvent, boolean bl) throws Exception {
        this.runOneCycle(tickEvent, bl);
    }

    public BarUpdateInfo getBarUpdateInfo() {
        return this.updateInfo;
    }
}

