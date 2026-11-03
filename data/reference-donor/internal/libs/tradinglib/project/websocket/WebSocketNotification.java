/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import org.json.JSONObject;

public class WebSocketNotification {
    public static void send(String string, String string2, String ... stringArray) {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("title", (Object)string);
        jSONObject.put("message", (Object)string2);
        SQWebSocketManager.addToDataQueue(new DataToSend("notification", jSONObject), stringArray);
    }

    public static void sendError(String string, String ... stringArray) {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("error", (Object)string);
        SQWebSocketManager.addToDataQueue(new DataToSend("notification", jSONObject), stringArray);
    }

    public static void sendSuccess(String string, String ... stringArray) {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("success", (Object)string);
        SQWebSocketManager.addToDataQueue(new DataToSend("notification", jSONObject), stringArray);
    }
}

