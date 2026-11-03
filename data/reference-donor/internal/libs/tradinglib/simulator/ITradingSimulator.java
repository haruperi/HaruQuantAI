/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TickEvent
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.ticksimulator.ITickSimulator
 *  com.strategyquant.lib.SettingsMap
 */
package com.strategyquant.tradinglib.simulator;

import com.strategyquant.datalib.TickEvent;
import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.ticksimulator.ITickSimulator;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.execution.ReservedBarsType;
import com.strategyquant.tradinglib.setup.BarUpdateInfo;
import com.strategyquant.tradinglib.strategy.MarketData;

public interface ITradingSimulator
extends IExecutionEngine {
    public void setConnection(String var1);

    public void setTestPrecision(int var1);

    public int getTestPrecision();

    public ITradingSimulator clone();

    public ITickSimulator getTickSimulator();

    public ReservedBarsType getReservedBarsType();

    public void eventNewTick(TickEvent var1, double var2, double var4);

    public void eventNewTick(TickEvent var1, double var2, double var4, BarUpdateInfo var6) throws TradingException;

    public void initialize(MarketData var1);

    public void destroy();

    public void eventEndOfTest();

    public int getEngineId();

    public void initSettings(SettingsMap var1) throws TradingException;

    public int getBarEventType();

    public boolean getApplyExitsAtTheEndOfRule();

    public void eventNoTrade();
}

