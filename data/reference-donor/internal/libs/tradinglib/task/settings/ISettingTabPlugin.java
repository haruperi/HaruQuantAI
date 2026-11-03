/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.ISQPlugin
 *  org.jdom2.Element
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.task.settings;

import com.strategyquant.pluginlib.ISQPlugin;
import com.strategyquant.tradinglib.task.settings.TaskSettingsData;
import com.strategyquant.tradinglib.taskImpl.ISQTask;
import org.jdom2.Element;
import org.json.JSONArray;
import org.json.JSONObject;

public interface ISettingTabPlugin
extends ISQPlugin {
    public String getSettingName();

    public String getName();

    public void readSettings(String var1, ISQTask var2, Element var3, TaskSettingsData var4);

    public void getStrategyConfigSettings(Element var1, JSONArray var2) throws Exception;

    public JSONObject getInitializationData() throws Exception;
}

