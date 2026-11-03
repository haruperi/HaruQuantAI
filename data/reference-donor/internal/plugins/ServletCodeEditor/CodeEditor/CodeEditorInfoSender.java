/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.Servlet.impl.CodeEditor;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import org.json.JSONObject;

public class CodeEditorInfoSender
extends SynchronizedWebSocketPublisher {
    private final DataToSend toSend = new DataToSend();
    private JSONObject data = null;

    public CodeEditorInfoSender() {
        this.toSend.setName("codeEditor");
        SQWebSocketManager.getInstance().addAppPublisher("SQEDITOR", (WebSocketPublisher)this);
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
}

