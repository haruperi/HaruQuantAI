/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.webguilib.servlet.HttpJSONServlet
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Settings.impl.Notification;

import com.strategyquant.webguilib.servlet.HttpJSONServlet;
import java.util.Map;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class NotificationServlet
extends HttpJSONServlet {
    private static final Logger Log = LoggerFactory.getLogger(NotificationServlet.class);

    protected String execute(String command, Map<String, String[]> parameterMap, String method) throws Exception {
        switch (command) {
            default: 
        }
        throw new Exception("Unknown command '" + command + "'.");
    }

    public JSONArray getTypes() {
        JSONArray types = new JSONArray();
        types.put((Object)new JSONObject().put("key", (Object)"email").put("name", (Object)"Email"));
        types.put((Object)new JSONObject().put("key", (Object)"popup").put("name", (Object)"Show popup"));
        return types;
    }
}

