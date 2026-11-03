/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.project.websocket;

import com.strategyquant.tradinglib.project.websocket.MultiProgressListener;
import com.strategyquant.tradinglib.project.websocket.MultiProgressPublisher;

public class DataManagerProgressListener
extends MultiProgressListener {
    public DataManagerProgressListener(String string, MultiProgressPublisher multiProgressPublisher) {
        super(string, multiProgressPublisher);
    }

    public void addLog(String string) {
        this.publisher.addStringCustomValue(this.key, "log", string, true);
    }

    public void setDataType(String string) {
        this.publisher.setCustomValue(this.key, "dataType", string);
    }

    public void setDownloadType(String string) {
        this.publisher.setCustomValue(this.key, "downloadType", string);
    }

    public void setSpeed(String string) {
        this.publisher.setCustomValue(this.key, "speed", string);
    }

    public void setEstimation(String string) {
        this.publisher.setCustomValue(this.key, "estimation", string);
    }
}

