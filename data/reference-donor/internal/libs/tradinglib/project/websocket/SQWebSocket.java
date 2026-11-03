/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.pluginlib.program.Program
 *  org.eclipse.jetty.websocket.api.Session
 *  org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose
 *  org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect
 *  org.eclipse.jetty.websocket.api.annotations.OnWebSocketError
 *  org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage
 *  org.eclipse.jetty.websocket.api.annotations.WebSocket
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.pluginlib.program.Program;
import com.strategyquant.tradinglib.project.websocket.ProjectFeeds;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;
import org.eclipse.jetty.websocket.api.Session;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketClose;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketConnect;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketError;
import org.eclipse.jetty.websocket.api.annotations.OnWebSocketMessage;
import org.eclipse.jetty.websocket.api.annotations.WebSocket;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

@WebSocket(maxTextMessageSize=0x100000)
public class SQWebSocket {
    private static final Logger Log = LoggerFactory.getLogger(SQWebSocket.class);
    private final CountDownLatch closeLatch;
    private Session session;
    private String productName;

    public SQWebSocket() {
        if (Log.isDebugEnabled()) {
            Log.debug("WebSocket initialized 1.");
        }
        this.closeLatch = new CountDownLatch(1);
    }

    @OnWebSocketConnect
    public void onConnect(Session session) {
        String string = session.getRemoteAddress().toString();
        if (Log.isDebugEnabled()) {
            Log.debug("Incoming connection from {}, protocol version: {}", (Object)string, (Object)session.getProtocolVersion());
        }
        this.session = session;
    }

    public String getUniqueId() {
        return this.productName;
    }

    @OnWebSocketMessage
    public void onMessage(String string) {
        Log.debug("Got message: '" + string + "'");
        this.processAction(new JSONObject(string));
    }

    @OnWebSocketError
    public void onError(Session session, Throwable throwable) {
        Log.debug("Websocket error", throwable);
    }

    @OnWebSocketClose
    public void onClose(int n, String string) {
        if (Log.isDebugEnabled()) {
            Log.debug("Connection closed. Product name: " + this.productName + ", status code: " + n + ", reason: " + string);
        }
        this.closeLatch.countDown();
        SQWebSocketManager.getInstance().removeClient(this.productName);
    }

    public boolean awaitClose(int n, TimeUnit timeUnit) throws InterruptedException {
        return this.closeLatch.await(n, timeUnit);
    }

    public void sendMessage(String string) throws Exception {
        if (this.session == null || !this.session.isOpen()) {
            return;
        }
        this.session.getRemote().sendString(string);
    }

    private void processAction(JSONObject jSONObject) {
        String string = jSONObject.getString("action");
        if (string == null) {
            return;
        }
        switch (string) {
            case "setup": {
                this.onSetup(jSONObject);
                return;
            }
            case "subscribe": {
                this.onSubscribe(jSONObject);
                return;
            }
            case "unsubscribe": {
                this.onUnsubscribe(jSONObject);
                return;
            }
            case "resolveCharts": {
                try {
                    String string2 = jSONObject.getString("format");
                    if (string2.equals("html")) {
                        Program.get((String)"SaverHTML").call("resolveCharts", new Object[]{jSONObject});
                    } else if (string2.equals("pdf")) {
                        Program.get((String)"SaverPDF").call("resolveCharts", new Object[]{jSONObject});
                    }
                }
                catch (Exception exception) {
                    Log.error("Cannot generate charts. Exc.", (Throwable)exception);
                }
                return;
            }
        }
    }

    private void onSetup(JSONObject jSONObject) {
        String string;
        String string2 = string = jSONObject.getString("app");
        if (string == null) {
            Log.error("Websocket setup error - Product name is null");
            return;
        }
        int n = 2;
        while (SQWebSocketManager.getInstance().containsClient(string2)) {
            string2 = string + "(" + n + ")";
            ++n;
        }
        this.productName = string2;
        SQWebSocketManager.getInstance().addClient(this);
        if (Log.isDebugEnabled()) {
            Log.debug("Connection opened. Product name: " + string2);
        }
    }

    private void onSubscribe(JSONObject jSONObject) {
        if (!jSONObject.has("projectName") || !jSONObject.has("channel")) {
            Log.error("Websocket subscription error - Product: '" + this.productName + "', JSON data: '" + jSONObject.toString() + "'");
            return;
        }
        String string = jSONObject.getString("projectName");
        String string2 = jSONObject.getString("channel");
        ProjectFeeds.subscribe(string, string2);
        SQWebSocketManager.getInstance().resetPublishersLastData(string);
    }

    private void onUnsubscribe(JSONObject jSONObject) {
        if (!jSONObject.has("projectName")) {
            return;
        }
        String string = jSONObject.getString("projectName");
        String string2 = jSONObject.getString("channel");
        if (string == null || string2 == null) {
            Log.error("Websocket unsubscription error - Project name: '" + string + "', channel: '" + string2 + "'");
            return;
        }
        ProjectFeeds.unsubscribe(string, string2);
    }
}

