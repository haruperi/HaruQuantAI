/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataToSend;

public interface WebSocketPublisher {
    public DataToSend getDataToSend() throws Exception;

    public void confirmBroadcast();

    public void resetLastData();
}

