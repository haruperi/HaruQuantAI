/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.results;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.results.IResultsGroupProvider;
import com.strategyquant.tradinglib.servlet.IServletPlugin;
import org.json.JSONObject;

public interface IResultPlugin
extends IServletPlugin {
    public boolean containsResult(ResultsGroup var1) throws Exception;

    public String getKey();

    public void setResultsGroupProvider(IResultsGroupProvider var1);

    public JSONObject getInitializationData() throws Exception;
}

