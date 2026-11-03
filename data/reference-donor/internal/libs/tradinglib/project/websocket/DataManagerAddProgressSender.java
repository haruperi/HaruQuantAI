/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataManagerAddProgressSender
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(DataManagerAddProgressSender.class);
    private DataToSend toSend = new DataToSend();
    private JSONObject data = null;
    private static DataManagerAddProgressSender instance;

    public static DataManagerAddProgressSender getInstance() {
        if (instance == null) {
            instance = new DataManagerAddProgressSender();
        }
        return instance;
    }

    private DataManagerAddProgressSender() {
        this.toSend.setName("DMDataAdd");
        SQWebSocketManager.getInstance().addAppPublisher("SQMANAGER", this);
    }

    @Override
    public DataToSend getData() {
        if (this.data != null) {
            this.toSend.setDataObject(new JSONObject(this.data.toString()));
            this.data = null;
            return this.toSend;
        }
        return null;
    }

    public void sendData(JSONObject jSONObject) {
        this.data = jSONObject;
    }

    @Override
    public void resetLastData() {
    }
}

