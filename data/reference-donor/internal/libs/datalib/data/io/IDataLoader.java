/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.historyData.ICryptable
 */
package com.strategyquant.datalib.data.io;

import com.strategyquant.datalib.data.io.ICanSeek;
import com.strategyquant.datalib.data.io.VersatileData;
import com.strategyquant.lib.historyData.ICryptable;

public interface IDataLoader
extends ICanSeek,
ICryptable {
    public boolean hasNextTick() throws Exception;

    public long nextTickTime() throws Exception;

    public void getNextTick(VersatileData var1) throws Exception;

    public void open() throws Exception;

    public void close() throws Exception;

    public boolean isOHLCData();

    public int getDecimalPlaces();

    public long getDateFrom();

    public long getTotalRecords() throws Exception;

    public String getDataFilePath();

    public boolean isCrypted();
}

