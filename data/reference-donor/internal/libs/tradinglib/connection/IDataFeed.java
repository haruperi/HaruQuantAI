/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.ChartDef
 */
package com.strategyquant.tradinglib.connection;

import com.strategyquant.datalib.ChartDef;
import com.strategyquant.tradinglib.connection.HistoryData;

public interface IDataFeed {
    public void registerSymbol(String var1) throws Exception;

    public boolean checkSymbolIsSupported(String var1);

    public HistoryData getHistoryData(ChartDef var1, int var2, long var3, long var5);
}

