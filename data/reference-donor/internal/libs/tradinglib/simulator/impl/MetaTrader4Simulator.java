/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.MetaTraderSimulatorHedging;

public class MetaTrader4Simulator
extends MetaTraderSimulatorHedging {
    @Override
    public void initSettings(SettingsMap settingsMap) throws TradingException {
        super.initSettings(settingsMap);
    }

    @Override
    public ITradingSimulator clone() {
        MetaTrader4Simulator metaTrader4Simulator = new MetaTrader4Simulator();
        metaTrader4Simulator.setTestPrecision(this.getTestPrecision());
        return metaTrader4Simulator;
    }

    @Override
    protected boolean checkPriceLevelCorrectness(int n, double d, double d2) {
        return !(n == 5 ? d >= d2 : (n == 6 ? d <= d2 : (n == 3 ? d <= d2 : n == 4 && d >= d2)));
    }

    @Override
    public boolean fillAtRealAskBidPrice() {
        return false;
    }

    @Override
    public boolean IsMarketOpen() {
        return true;
    }

    @Override
    protected double getSLPTFilledPrice(double d, double d2) {
        return d2;
    }

    @Override
    public int getEngineId() {
        return -659455871;
    }
}

