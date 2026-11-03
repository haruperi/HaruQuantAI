/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Portfolio.impl.Composer;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class PortfolioComposerResultsSender
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(PortfolioComposerResultsSender.class);
    private DataToSend toSend = new DataToSend();
    private JSONObject data = null;

    public PortfolioComposerResultsSender() {
        this.toSend.setName("portfolioComposer");
        SQWebSocketManager.getInstance().addAppPublisher("PORTFOLIOCOMPOSER", (WebSocketPublisher)this);
    }

    public DataToSend getData() {
        if (this.data != null) {
            this.toSend.setDataObject(new JSONObject(this.data.toString()));
            this.data = null;
            return this.toSend;
        }
        return null;
    }

    public void sendData(JSONObject data) {
        this.data = data;
    }

    public void resetLastData() {
    }

    public void progress(int pct, String message) {
        if (this.data == null) {
            this.data = new JSONObject();
        }
        this.data.put("progress", pct);
        this.data.put("message", (Object)message);
    }
}

