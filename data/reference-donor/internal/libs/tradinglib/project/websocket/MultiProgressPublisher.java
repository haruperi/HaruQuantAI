/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketNotification;
import java.util.HashMap;
import java.util.LinkedList;
import java.util.List;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MultiProgressPublisher
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(MultiProgressPublisher.class);
    private HashMap<String, MultiProgressListener> listeners = new HashMap();
    private List<String> listenersForRemove = new LinkedList<String>();
    private DataToSend dataToSend;
    private JSONArray jsonData;
    private String lastDataHash;
    private String appCode;

    public MultiProgressPublisher(String string, String string2) {
        SQWebSocketManager.getInstance().addAppPublisher(string2, this);
        this.appCode = string2;
        this.jsonData = new JSONArray();
        this.dataToSend = new DataToSend(string, this.jsonData);
    }

    public synchronized MultiProgressListener createListener(String string) {
        if (!this.listeners.containsKey(string)) {
            this.listeners.put(string, this.performCreateListener(string));
        }
        MultiProgressListener multiProgressListener = this.listeners.get(string);
        multiProgressListener.reset();
        return multiProgressListener;
    }

    public synchronized MultiProgressListener getListener(String string) {
        if (!this.listeners.containsKey(string)) {
            return null;
        }
        return this.listeners.get(string);
    }

    public synchronized void removeListener(String string) {
        this.listenersForRemove.add(string);
    }

    protected MultiProgressListener performCreateListener(String string) {
        return new MultiProgressListener(string, this);
    }

    public synchronized void setProgress(String string, int n) {
        MultiProgressListener multiProgressListener = this.createListener(string);
        JSONObject jSONObject = multiProgressListener.jsonData;
        jSONObject.put("pct", n);
    }

    public synchronized void setProgress(String string, int n, String string2) {
        MultiProgressListener multiProgressListener = this.createListener(string);
        this.setProgress(string, n);
        JSONObject jSONObject = multiProgressListener.jsonData;
        jSONObject.put("message", (Object)string2);
    }

    public synchronized void setMessage(String string, String string2) {
        MultiProgressListener multiProgressListener = this.createListener(string);
        JSONObject jSONObject = multiProgressListener.jsonData;
        jSONObject.put("message", (Object)string2);
    }

    public synchronized void setCustomValue(String string, String string2, Object object) {
        MultiProgressListener multiProgressListener = this.createListener(string);
        JSONObject jSONObject = multiProgressListener.jsonData;
        jSONObject.put(string2, object);
    }

    public synchronized void addStringCustomValue(String string, String string2, String string3, boolean bl) {
        MultiProgressListener multiProgressListener = this.createListener(string);
        JSONObject jSONObject = multiProgressListener.jsonData;
        if (jSONObject.has(string2)) {
            String string4 = (String)jSONObject.get(string2);
            string3 = bl ? string3 + string4 : string4 + string3;
        }
        jSONObject.put(string2, (Object)string3);
    }

    public synchronized void clearAllCustomValues(String string) {
        for (MultiProgressListener multiProgressListener : this.listeners.values()) {
            JSONObject jSONObject = multiProgressListener.jsonData;
            jSONObject.remove(string);
        }
    }

    @Override
    protected synchronized DataToSend getData() {
        for (int i = this.jsonData.length() - 1; i >= 0; --i) {
            this.jsonData.remove(i);
        }
        for (String string : this.listeners.keySet()) {
            JSONObject jSONObject = this.listeners.get(string).getData();
            if (jSONObject == null) continue;
            this.jsonData.put((Object)jSONObject);
        }
        if (this.lastDataHash == null || !this.jsonData.toString().equals(this.lastDataHash)) {
            this.lastDataHash = this.jsonData.toString();
            return this.dataToSend;
        }
        return null;
    }

    public void reset() {
        this.lastDataHash = null;
    }

    @Override
    public void resetLastData() {
        this.lastDataHash = null;
    }

    public void onError(String string) {
        WebSocketNotification.sendError(string, this.appCode);
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    protected void handleConfirmBroadcast() {
        super.handleConfirmBroadcast();
        MultiProgressPublisher multiProgressPublisher = this;
        synchronized (multiProgressPublisher) {
            for (String string : this.listenersForRemove) {
                this.listeners.remove(string);
            }
            this.listenersForRemove.clear();
        }
    }
}

