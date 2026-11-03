/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.DataManager.impl.Connections;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ConnectionInfoSender
extends SynchronizedWebSocketPublisher {
    private static final Logger Log = LoggerFactory.getLogger(ConnectionInfoSender.class);
    private static ConnectionInfoSender instance;
    private boolean stop = true;

    public ConnectionInfoSender() {
        SQWebSocketManager.getInstance().addAppPublisher("SQMANAGER", (WebSocketPublisher)this);
        instance = this;
    }

    public static ConnectionInfoSender getInstance() {
        if (instance == null) {
            new ConnectionInfoSender();
        }
        return instance;
    }

    public void start() {
        this.stop = false;
    }

    public void stop() {
        this.stop = true;
    }

    public DataToSend getData() {
        if (!this.stop) {
            return WSDataObjects.getConnections();
        }
        return null;
    }

    public void resetLastData() {
    }
}

