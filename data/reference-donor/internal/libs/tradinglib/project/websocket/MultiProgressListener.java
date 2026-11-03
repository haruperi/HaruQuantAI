/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.IProgressListener
 *  org.json.JSONObject
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.project.websocket.MultiProgressPublisher;
import org.json.JSONObject;

public class MultiProgressListener
implements IProgressListener {
    public static final String SYMBOL_TOTAL = "TotalProgressSymbol";
    protected String key;
    public JSONObject jsonData;
    protected MultiProgressPublisher publisher;
    private String lastMessage;
    private String lastJson;

    public MultiProgressListener(String string, MultiProgressPublisher multiProgressPublisher) {
        this.key = string;
        this.publisher = multiProgressPublisher;
        this.jsonData = new JSONObject();
        this.jsonData.put("key", (Object)string);
    }

    public void setMessage(String string) {
        this.publisher.setMessage(this.key, string);
    }

    public void onStart() {
    }

    public void onProgress(double d) {
        this.publisher.setProgress(this.key, (int)d);
    }

    public void onPause() {
        this.publisher.setCustomValue(this.key, "paused", true);
    }

    public void onContinue() {
        this.publisher.setCustomValue(this.key, "paused", false);
    }

    public void onFinish() {
        this.publisher.setProgress(this.key, 100);
    }

    public void onError(String string) {
        this.publisher.setMessage(this.key, string);
        this.publisher.setProgress(this.key, -1);
        this.publisher.onError(string);
    }

    public void onConfirm(String string) {
    }

    public void setStep(int n) {
    }

    public void reset() {
        this.publisher.reset();
    }

    public JSONObject getData() {
        String string;
        String string2 = string = this.jsonData.has("message") ? this.jsonData.getString("message") : null;
        if (!(string == null || this.lastMessage != null && string.equals(this.lastMessage))) {
            this.jsonData.put("logStr", (Object)string);
        } else {
            this.jsonData.remove("logStr");
        }
        this.lastMessage = string;
        String string3 = this.jsonData.toString();
        boolean bl = string3.equals(this.lastJson);
        this.lastJson = string3;
        if (bl) {
            double d;
            if (SYMBOL_TOTAL.equals(this.key) && this.jsonData.has("pct") && (d = this.jsonData.getDouble("pct")) < 100.0) {
                return this.jsonData;
            }
            return null;
        }
        return this.jsonData;
    }
}

