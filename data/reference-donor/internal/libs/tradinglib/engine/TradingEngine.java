/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.TradingException
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.lib.SettingsMap
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.engine;

import com.strategyquant.datalib.TradingException;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.tradinglib.ChartSetup;
import com.strategyquant.tradinglib.StrategyBase;
import com.strategyquant.tradinglib.Trader;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;
import com.strategyquant.tradinglib.engine.TradingSetup;
import com.strategyquant.tradinglib.execution.IExecutionEngine;
import com.strategyquant.tradinglib.setup.Portfolio;
import java.util.ArrayList;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TradingEngine {
    public static final Logger Log = LoggerFactory.getLogger((String)"TradingEngine");
    public static final int TYPE_LIVETRADING = 0;
    public static final int TYPE_BACKTEST = 1;
    private static TradingEngine instance = null;
    private Portfolio portfolio = new Portfolio();
    private ConnectionManager connectionManager;

    public static void init(TradingEngine tradingEngine) throws Exception {
        if (instance != null) {
            throw new Exception("TradingEngine.init() called more than once!");
        }
        instance = tradingEngine;
    }

    public static TradingEngine getLiveEngine() {
        return instance;
    }

    public TradingEngine(ConnectionManager connectionManager) {
        this.connectionManager = connectionManager;
    }

    public TradingSetup addSetup(ChartSetup chartSetup, SettingsMap settingsMap, StrategyBase strategyBase, String ... stringArray) throws Exception {
        String string;
        if (!(chartSetup = chartSetup.getClone()).isCreatedUsingBackload()) {
            throw new TradingException("You have to create Chart Setup with constructor that has backloadType and backloadNumber, not with constructor that uses date from - to !");
        }
        if (stringArray.length == 0) {
            stringArray = new String[]{chartSetup.getCharts().get(0).getConnectionName()};
            string = stringArray[0];
        } else {
            string = stringArray[0];
        }
        strategyBase.setTradeControllers(string, this.getTradeControllers(stringArray));
        TradingSetup tradingSetup = new TradingSetup(this, -659455871, chartSetup, settingsMap, strategyBase);
        this.portfolio.add(tradingSetup);
        return tradingSetup;
    }

    private Trader[] getTradeControllers(String[] stringArray) throws DataException {
        Trader[] traderArray = new Trader[stringArray.length];
        for (int i = 0; i < stringArray.length; ++i) {
            String string = stringArray[i];
            traderArray[i] = new Trader(string, this.getExecutionEngine(string));
        }
        return traderArray;
    }

    private IExecutionEngine getExecutionEngine(String string) throws DataException {
        Connection connection = this.getConnectionManager().getConnection(string);
        if (!connection.isExecutionEngine()) {
            throw new DataException(1, "Connection '" + connection.getConnectionName() + "' is not an execution engine !");
        }
        if (!(connection instanceof IExecutionEngine)) {
            throw new DataException(1, "Connection '" + connection.getConnectionName() + "' doesn't implement an execution engine !");
        }
        return (IExecutionEngine)((Object)connection);
    }

    public void deinitialize() {
    }

    public ConnectionManager getConnectionManager() {
        return this.connectionManager;
    }

    public ArrayList<TradingSetup> getTradingSetups() {
        return this.portfolio.getTradingSetups();
    }

    public void remove(TradingSetup tradingSetup) throws Exception {
        tradingSetup.stop();
        this.portfolio.remove(tradingSetup);
    }

    public void removeAll() throws Exception {
        for (TradingSetup tradingSetup : this.portfolio.getTradingSetups()) {
            tradingSetup.stop();
        }
        this.portfolio.clear();
    }

    public TradingSetup getSetupById(int n) {
        for (TradingSetup tradingSetup : this.portfolio.getTradingSetups()) {
            if (tradingSetup.getSetupId() != n) continue;
            return tradingSetup;
        }
        return null;
    }
}

