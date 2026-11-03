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
import com.strategyquant.tradinglib.simulator.impl.MetaTrader4Simulator;

public class JForexSimulator
extends MetaTrader4Simulator {
    @Override
    public void initSettings(SettingsMap settingsMap) throws TradingException {
        super.initSettings(settingsMap);
    }

    @Override
    public ITradingSimulator clone() {
        JForexSimulator jForexSimulator = new JForexSimulator();
        jForexSimulator.setTestPrecision(this.getTestPrecision());
        return jForexSimulator;
    }

    @Override
    protected boolean checkPriceLevelCorrectness(int n, double d, double d2) {
        return !(n == 5 ? d >= d2 : (n == 6 ? d <= d2 : (n == 3 ? d <= d2 : n == 4 && d >= d2)));
    }

    @Override
    public boolean fillAtRealAskBidPrice() {
        return true;
    }

    @Override
    protected double getSLPTFilledPrice(double d, double d2) {
        return d;
    }

    @Override
    public int getEngineId() {
        return -659455871;
    }
}

