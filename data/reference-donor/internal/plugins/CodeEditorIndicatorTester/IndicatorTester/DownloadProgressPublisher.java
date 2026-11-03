/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.indicatorTester.IndicatorTesterConfig
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher
 *  com.strategyquant.tradinglib.project.websocket.WebSocketPublisher
 *  org.jdom2.Element
 *  org.json.JSONObject
 */
package com.strategyquant.plugin.CodeEditor.impl.IndicatorTester;

import com.strategyquant.indicatorTester.IndicatorTesterConfig;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.SynchronizedWebSocketPublisher;
import com.strategyquant.tradinglib.project.websocket.WebSocketPublisher;
import java.util.concurrent.locks.StampedLock;
import org.jdom2.Element;
import org.json.JSONObject;

public class DownloadProgressPublisher
extends SynchronizedWebSocketPublisher
implements IProgressListener {
    private static DownloadProgressPublisher instance;
    private DataToSend info = new DataToSend("TestsDownloadStatus");
    private JSONObject status = new JSONObject();
    private String lastData = "";
    private StampedLock lock = new StampedLock();

    private DownloadProgressPublisher() {
        instance = this;
        this.info.setDataObject(this.status);
        SQWebSocketManager.getInstance().addAppPublisher("SQEDITOR", (WebSocketPublisher)this);
    }

    public static DownloadProgressPublisher get() {
        return instance == null ? new DownloadProgressPublisher() : instance;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    protected DataToSend getData() {
        long stamp = this.lock.readLock();
        try {
            String newData = this.status.toString();
            if (!this.lastData.equals(newData)) {
                this.lastData = newData;
                DataToSend dataToSend = this.info;
                return dataToSend;
            }
            DataToSend dataToSend = null;
            return dataToSend;
        }
        finally {
            this.lock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void setMessage(String message) {
        long stamp = this.lock.writeLock();
        try {
            this.status.put("info", (Object)message);
            this.status.put("error", false);
            this.status.put("xmlConfig", false);
        }
        finally {
            this.lock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void onProgress(double percent) {
        long stamp = this.lock.writeLock();
        try {
            this.status.put("percent", (int)percent);
            if (percent != 100.0) {
                this.status.put("xmlConfig", false);
                this.status.put("filePath", false);
            } else {
                this.status.put("xmlConfig", (Object)XMLUtil.elementToString((Element)IndicatorTesterConfig.getConfig()));
                this.status.put("filePath", (Object)IndicatorTesterConfig.defaultConfigFilePath);
            }
        }
        finally {
            this.lock.unlock(stamp);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void onError(String errorMsg) {
        long stamp = this.lock.writeLock();
        try {
            this.status.put("error", (Object)errorMsg);
        }
        finally {
            this.lock.unlock(stamp);
        }
    }

    public void resetLastData() {
        this.lastData = "";
    }

    public void onStart() {
    }

    public void onFinish() {
    }

    public void onConfirm(String confirmMsg) {
    }

    public void setStep(int step) {
    }

    public void onPause() {
    }

    public void onContinue() {
    }
}

