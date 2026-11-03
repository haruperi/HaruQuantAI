/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.options.TradingOptions
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Options;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.options.TradingOptions;
import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SettingsOptionsServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(SettingsOptionsServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            case "list": {
                return this.onList(parameterMap);
            }
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    private String onList(Map<String, String[]> parameterMap) throws Exception {
        JSONObject response = new JSONObject();
        response.put("parameters", (Object)TradingOptions.list());
        response.put("success", (Object)L.t((String)"Options listed.", (Object[])new Object[0]));
        return response.toString();
    }
}

