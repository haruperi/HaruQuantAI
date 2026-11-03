/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 *  com.strategyquant.datalib.data.DataException
 *  com.strategyquant.datalib.data.DataManager
 */
package com.strategyquant.tradinglib.backtest;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.datalib.data.DataException;
import com.strategyquant.datalib.data.DataManager;
import com.strategyquant.tradinglib.backtest.BacktestDataFeed;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.HistoryData;
import com.strategyquant.tradinglib.connection.IDataFeed;

public class BacktestConnection
extends Connection
implements IDataFeed {
    private BacktestDataFeed backtestDataFeed;

    public BacktestConnection(String string, BacktestDataFeed backtestDataFeed) throws DataException {
        super(null, string, null, null);
        this.backtestDataFeed = backtestDataFeed;
        if (!DataManager.checkConnectionExists((String)string)) {
            throw new DataException(1, "Connection with name '" + string + "' doesn't exist!");
        }
    }

    @Override
    public void initializeEngines() {
        this.setDataFeed(this);
    }

    @Override
    public void connect() {
    }

    @Override
    public void disconnect() {
    }

    @Override
    public void registerSymbol(String string) {
    }

    @Override
    public boolean checkSymbolIsSupported(String string) {
        return DataManager.checkDataExists((String)this.connectionName, (String)string);
    }

    @Override
    public boolean isConnected() {
        return true;
    }

    @Override
    public String getType() {
        return "Backtest";
    }

    @Override
    public String getStatus() {
        return "Connected";
    }

    @Override
    public String getPluginName() {
        return "BacktestConnection";
    }

    @Override
    public HistoryData getHistoryData(ChartDef chartDef, int n, long l, long l2) {
        return null;
    }
}

