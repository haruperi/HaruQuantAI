/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.simulator.impl;

import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.simulator.ITradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.AbstractTradingSimulator;
import com.strategyquant.tradinglib.simulator.impl.JForexSimulator;
import com.strategyquant.tradinglib.simulator.impl.MetaTrader4Simulator;
import com.strategyquant.tradinglib.simulator.impl.MetaTrader5SimulatorHedging;
import com.strategyquant.tradinglib.simulator.impl.MetaTrader5SimulatorNetting;
import com.strategyquant.tradinglib.simulator.impl.MultiChartsSimulator;
import com.strategyquant.tradinglib.simulator.impl.TradestationSimulator;

public class TraderSimulators {
    public static ITradingSimulator getMT4Simulator() {
        return new MetaTrader4Simulator();
    }

    public static ITradingSimulator getMT5Simulator(boolean bl, byte by) {
        if (bl) {
            return new MetaTrader5SimulatorHedging(by);
        }
        return new MetaTrader5SimulatorNetting(by);
    }

    public static ITradingSimulator getSimulator(boolean bl, boolean bl2, byte by) {
        if (bl) {
            return TraderSimulators.getMT5Simulator(bl2, by);
        }
        return TraderSimulators.getMT4Simulator();
    }

    public static ITradingSimulator getSimulator(ChartSetup chartSetup) throws Exception {
        AbstractTradingSimulator abstractTradingSimulator = null;
        switch (chartSetup.getBacktestEngine()) {
            case -659455871: {
                abstractTradingSimulator = new MetaTrader4Simulator();
                break;
            }
            case 395961824: {
                abstractTradingSimulator = new MetaTrader5SimulatorHedging(4);
                break;
            }
            case 1441180233: {
                abstractTradingSimulator = new MetaTrader5SimulatorNetting(4);
                break;
            }
            case 56756755: {
                abstractTradingSimulator = new TradestationSimulator();
                break;
            }
            case 938213070: {
                abstractTradingSimulator = new MultiChartsSimulator();
                break;
            }
            case 1949519549: {
                abstractTradingSimulator = new JForexSimulator();
                break;
            }
            case -1816889229: 
            case 1316847364: {
                abstractTradingSimulator = new MetaTrader4Simulator();
                break;
            }
            default: {
                throw new Exception("Unknown backtest engine with code " + chartSetup.getBacktestEngine());
            }
        }
        abstractTradingSimulator.setTestPrecision(chartSetup.getTestPrecision());
        return abstractTradingSimulator;
    }
}

