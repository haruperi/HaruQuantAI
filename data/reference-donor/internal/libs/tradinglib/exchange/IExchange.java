/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.json.JSONArray
 */
package com.strategyquant.tradinglib.exchange;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.exchange.SymbolInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.io.Serializable;
import org.json.JSONArray;

public interface IExchange
extends ISQPlugin,
Serializable {
    public String getName();

    public JSONArray getSymbols() throws Exception;

    public void cancel();

    public void pause();

    public void restart();

    public void performDownload(String var1, DataManagerProgressListener var2, DataInfo var3, ImportInfo var4) throws Exception;

    public boolean isCanceled();

    public IExchange clone();

    public String convertTimeframe(String var1) throws Exception;

    public JSONArray availableTimeframes();

    public boolean checkSymbolExists(String var1);

    public SymbolInfo getSymbolInfo(String var1);
}

