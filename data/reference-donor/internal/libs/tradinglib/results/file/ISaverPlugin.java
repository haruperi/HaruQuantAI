/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 */
package com.strategyquant.tradinglib.results.file;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.ResultsGroup;
import java.util.Map;

public interface ISaverPlugin
extends ISQPlugin {
    public String[] getFileExtensions();

    public void save(ResultsGroup var1, String var2, Map<String, String[]> var3) throws Exception;

    public ISaverPlugin clone();
}

