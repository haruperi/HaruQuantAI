/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.ValuesMap
 *  com.strategyquant.pluginlib.ISQPlugin
 */
package com.strategyquant.tradinglib.plugindef.connection;

import com.strategyquant.lib.ValuesMap;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.connection.Connection;
import com.strategyquant.tradinglib.connection.ConnectionManager;

public interface IConnectionPlugin
extends ISQPlugin {
    public String getPluginName();

    public boolean isDataFeed();

    public boolean isExecutionEngine();

    public Connection createConnection(ConnectionManager var1, String var2, ValuesMap var3) throws Exception;
}

