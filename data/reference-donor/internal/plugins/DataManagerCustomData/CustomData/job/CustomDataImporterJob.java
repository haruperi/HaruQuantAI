/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.customData.CustomDataInfo
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 */
package com.strategyquant.plugin.DataManager.impl.CustomData.job;

import com.strategyquant.datalib.customData.CustomDataInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataManager.impl.CustomData.job.CustomDataImporter;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;

public class CustomDataImporterJob
extends GridJob<Void> {
    private CustomDataImporter dataImporter = new CustomDataImporter();
    private IProgressListener listener;
    private CustomDataInfo dataInfo;
    private ImportDataInfo importInfo;

    public CustomDataImporterJob(String jobId, IProgressListener listener, CustomDataInfo dataInfo, ImportDataInfo importInfo) {
        super(jobId, 0, null);
        this.listener = listener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
    }

    public Void call() throws Exception {
        try {
            this.listener.setMessage(L.t((String)"Starting custom data import...", (Object[])new Object[0]));
            this.listener.onProgress(1.0);
            this.dataImporter.performImport(this.listener, this.dataInfo, this.importInfo);
            this.listener.onProgress(100.0);
            this.listener.setMessage(this.dataImporter.isCanceled() ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        }
        catch (Exception e) {
            this.listener.onError(e.getMessage());
        }
        this.sendRefreshMessage();
        return null;
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getCustomData((String)this.dataInfo.name, (String)"import"), (String[])new String[]{"SQUANT", "QDM"});
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    public void messageReceived(GridMessage message) {
        super.messageReceived(message);
        switch (message.getMessageID()) {
            case 4: {
                this.dataImporter.cancel();
                break;
            }
            case 2: {
                this.dataImporter.pause();
                break;
            }
            case 3: {
                this.dataImporter.restart();
            }
        }
    }
}

