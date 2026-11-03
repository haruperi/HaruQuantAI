/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 */
package com.strategyquant.tradinglib.results.file;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.ResultsGroup;

public interface ILoaderPlugin
extends ISQPlugin {
    public String[] getFileExtensions();

    public ResultsGroup load(String var1, boolean var2, String var3, String var4) throws Exception;

    public ResultsGroup finishLoad(ResultsGroup var1) throws Exception;
}

