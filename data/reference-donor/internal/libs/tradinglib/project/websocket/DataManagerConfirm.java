/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.json.JSONArray
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import org.json.JSONArray;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DataManagerConfirm {
    private static final Logger Log = LoggerFactory.getLogger(DataManagerConfirm.class);
    public static final String ActionOverwriteAll = "overwrite_all";
    public static final String ActionOverwrite = "overwrite";
    public static final String ActionSkip = "skip";
    public static final String ActionCancel = "cancel";
    private DataToSend confirmData;
    private Thread waitingThread;
    private String confirmedAction = null;
    private static DataManagerConfirm instance = null;

    public static DataManagerConfirm get() {
        if (instance == null) {
            instance = new DataManagerConfirm();
        }
        return instance;
    }

    public DataManagerConfirm() {
        JSONObject jSONObject = new JSONObject();
        jSONObject.put("options", (Object)new JSONArray().put((Object)new JSONObject().put("title", (Object)L.t((String)"Overwrite All", (Object[])new Object[0])).put("key", (Object)ActionOverwriteAll)).put((Object)new JSONObject().put("title", (Object)L.t((String)"Overwrite", (Object[])new Object[0])).put("key", (Object)ActionOverwrite)).put((Object)new JSONObject().put("title", (Object)L.t((String)"Skip", (Object[])new Object[0])).put("key", (Object)ActionSkip)).put((Object)new JSONObject().put("title", (Object)L.t((String)"Cancel import", (Object[])new Object[0])).put("key", (Object)ActionCancel)));
        this.confirmData = new DataToSend("DMConfirmation", jSONObject);
    }

    public void awaitConfirmation(String string, String string2) throws Exception {
        this.confirmData.getDataObject().put("title", (Object)string);
        this.confirmData.getDataObject().put("message", (Object)string2);
        SQWebSocketManager.addToDataQueue(this.confirmData, "SQMANAGER");
        if (this.waitingThread == null || !this.waitingThread.isAlive()) {
            this.confirmedAction = null;
            this.waitingThread = new Thread(){

                @Override
                public void run() {
                    while (DataManagerConfirm.this.confirmedAction == null) {
                        try {
                            Thread.sleep(50L);
                        }
                        catch (Exception exception) {}
                    }
                }
            };
            this.waitingThread.start();
            try {
                this.waitingThread.join();
            }
            catch (InterruptedException interruptedException) {
                Log.error("Waiting for confirmation interrupted.", (Throwable)interruptedException);
            }
        } else {
            throw new Exception("Confirmation in progress");
        }
    }

    public void setConfirmedAction(String string) {
        this.confirmedAction = string;
    }

    public String getConfirmedAction() {
        return this.confirmedAction;
    }
}

