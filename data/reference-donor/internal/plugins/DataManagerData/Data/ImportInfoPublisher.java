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
package com.strategyquant.plugin.DataManager.impl.Data;

import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import org.json.JSONObject;

public class ImportInfoPublisher
extends SynchronizedWebSocketPublisher {
    private DataToSend toSend = new DataToSend();
    private volatile boolean newData = true;
    private String infoMessage = "";
    private int step;
    private static ImportInfoPublisher instance;

    public ImportInfoPublisher() {
        this.toSend.setName("dataImportProgress");
        this.toSend.setDataObject(new JSONObject().put("progress", 0));
        SQWebSocketManager.getInstance().addAppPublisher("SQMANAGER", (WebSocketPublisher)this);
        instance = this;
    }

    private static ImportInfoPublisher get() {
        if (instance == null) {
            new ImportInfoPublisher();
        }
        return instance;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void setProgress(int percentage) {
        DataToSend dataToSend = ImportInfoPublisher.get().toSend;
        synchronized (dataToSend) {
            JSONObject obj = ImportInfoPublisher.get().toSend.getDataObject();
            obj.remove("error");
            obj.remove("confirm");
            obj.remove("confirmLabel");
            obj.put("step", ImportInfoPublisher.instance.step);
            obj.put("message", (Object)ImportInfoPublisher.instance.infoMessage);
            obj.put("progress", percentage);
            ImportInfoPublisher.get().newData = true;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void setError(String error) {
        DataToSend dataToSend = ImportInfoPublisher.get().toSend;
        synchronized (dataToSend) {
            JSONObject obj = ImportInfoPublisher.get().toSend.getDataObject();
            obj.remove("progress");
            obj.remove("confirm");
            obj.remove("confirmLabel");
            obj.remove("step");
            obj.put("message", (Object)ImportInfoPublisher.instance.infoMessage);
            obj.put("error", (Object)error);
            ImportInfoPublisher.get().newData = true;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public static void setConfirmation(String label, String message) {
        DataToSend dataToSend = ImportInfoPublisher.get().toSend;
        synchronized (dataToSend) {
            JSONObject obj = ImportInfoPublisher.get().toSend.getDataObject();
            obj.remove("progress");
            obj.remove("error");
            obj.remove("step");
            obj.put("message", (Object)ImportInfoPublisher.instance.infoMessage);
            obj.put("confirm", (Object)message);
            obj.put("confirmLabel", (Object)label);
            ImportInfoPublisher.get().newData = true;
        }
    }

    public static void setMessage(String message) {
        ImportInfoPublisher.get().infoMessage = message;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public DataToSend getData() {
        DataToSend dataToSend = this.toSend;
        synchronized (dataToSend) {
            if (this.newData) {
                this.newData = false;
                return this.toSend;
            }
            return null;
        }
    }

    public void resetLastData() {
        this.newData = true;
    }

    public static void setStep(int step) {
        ImportInfoPublisher.get().step = step;
    }
}

