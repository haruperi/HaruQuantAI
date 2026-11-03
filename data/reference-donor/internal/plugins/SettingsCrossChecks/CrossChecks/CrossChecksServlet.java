/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.SQPluginManager
 *  com.strategyquant.tradinglib.crosscheck.ICrossCheck
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.CrossChecks;

import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CrossChecksServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(CrossChecksServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            default: 
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONArray list() throws Exception {
        JSONArray crosschecks = new JSONArray();
        for (ICrossCheck plugin : SQPluginManager.getPlugins(ICrossCheck.class)) {
            JSONObject crosscheck = new JSONObject();
            crosscheck.put("use", true);
            crosscheck.put("type", plugin.getType());
            crosscheck.put("title", (Object)plugin.getName());
            crosscheck.put("desc", (Object)plugin.getDescription());
            crosscheck.put("name", (Object)plugin.getSettingName());
            crosscheck.put("position", plugin.getPreferredPosition());
            crosscheck.put("forEngine", (Object)plugin.forEngine());
            crosscheck.put("disabledForSpecialTrial", plugin.disabledForSpecialTrial());
            crosschecks.put((Object)crosscheck);
        }
        return crosschecks;
    }
}

