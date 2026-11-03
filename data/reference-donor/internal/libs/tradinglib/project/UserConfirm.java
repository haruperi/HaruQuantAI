/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import org.json.JSONObject;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class UserConfirm {
    private static final Logger Log = LoggerFactory.getLogger(UserConfirm.class);
    protected String projectName;
    private DataToSend confirmData;
    private Thread waitingThread;
    private boolean confirmed = false;
    private volatile boolean resolved = false;

    public UserConfirm(String string) {
        this.projectName = string;
        this.confirmData = new DataToSend("confirmation", new JSONObject());
    }

    public void awaitConfirmation(String string, String string2) throws Exception {
        this.awaitConfirmation(string, string2, null);
    }

    public void awaitConfirmation(String string, String string2, JSONObject jSONObject) throws Exception {
        this.confirmData.getDataObject().put("projectName", (Object)this.projectName);
        this.confirmData.getDataObject().put("title", (Object)string);
        this.confirmData.getDataObject().put("message", (Object)string2);
        if (jSONObject != null) {
            this.confirmData.getDataObject().put("additionalData", (Object)jSONObject);
        } else {
            this.confirmData.getDataObject().remove("additionalData");
        }
        SQWebSocketManager.addToDataQueue(this.confirmData, SQWebSocketManager.getProductCode(this.projectName));
        if (this.waitingThread == null || !this.waitingThread.isAlive()) {
            this.resolved = false;
            this.waitingThread = new Thread(){

                @Override
                public void run() {
                    while (!UserConfirm.this.resolved) {
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

    public void setConfirmed(boolean bl) {
        this.confirmed = bl;
        this.resolved = true;
    }

    public boolean isConfirmed() {
        return this.confirmed;
    }

    public void setProjectName(String string) {
        this.projectName = string;
    }
}

