/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.MultiProgressPublisher;
import org.json.JSONObject;

public class DataManagerDataProgress
extends MultiProgressPublisher {
    private static DataManagerDataProgress instance;

    public static DataManagerDataProgress get() {
        if (instance == null) {
            instance = new DataManagerDataProgress();
        }
        return instance;
    }

    public DataManagerDataProgress() {
        super("DMDataProgresses", "SQMANAGER");
    }

    @Override
    protected MultiProgressListener performCreateListener(String string) {
        return new DataManagerProgressListener(string, this);
    }

    @Override
    protected void handleConfirmBroadcast() {
        super.handleConfirmBroadcast();
        this.clearAllCustomValues("log");
    }

    public MultiProgressListener createListener(String string, String string2) {
        MultiProgressListener multiProgressListener = super.createListener(string);
        JSONObject jSONObject = multiProgressListener.jsonData;
        jSONObject.put("actionLink", (Object)string2);
        return multiProgressListener;
    }
}

