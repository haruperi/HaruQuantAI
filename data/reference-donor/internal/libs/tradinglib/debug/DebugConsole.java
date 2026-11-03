/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.SQTime
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.debug;

import com.strategyquant.lib.SQTime;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DebugConsole
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(DebugConsole.class);
    private static DebugConsole instance = null;
    private static final int MAX_LOG_ENTRIES = 1000;
    JSONArray data = new JSONArray();
    DataToSend toSend = new DataToSend("DebugConsoleLog");

    private DebugConsole() {
        SQWebSocketManager.getInstance().addAppPublisher("DEBUGCONSOLE", this);
    }

    public static DebugConsole getInstance() {
        if (instance == null) {
            instance = new DebugConsole();
        }
        return instance;
    }

    public static void log(String string, String string2) {
        DebugConsole.getInstance()._log(string, string2);
    }

    private void _log(String string, String string2) {
        if (this.data.length() >= 1000) {
            return;
        }
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("time", (Object)SQTime.getLogTime((boolean)false, (boolean)false));
        jSONObject.put("category", (Object)string);
        jSONObject.put("message", (Object)string2);
        this.data.put((Object)jSONObject);
    }

    @Override
    public void resetLastData() {
    }

    @Override
    protected DataToSend getData() {
        if (this.data.length() > 0) {
            this.toSend.setDataObject(this.data);
            this.data = new JSONArray();
            return this.toSend;
        }
        return null;
    }
}

