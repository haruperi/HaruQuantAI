/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.datalib.data.io.ImportDataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.utils.IProgressListener
 *  com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress
 *  com.strategyquant.tradinglib.project.websocket.DataToSend
 *  com.strategyquant.tradinglib.project.websocket.SQWebSocketManager
 *  com.strategyquant.tradinglib.project.websocket.WSDataObjects
 */
package com.strategyquant.plugin.DataSource.impl.Files.job;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.datalib.data.io.ImportDataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.utils.IProgressListener;
import com.strategyquant.plugin.DataSource.impl.Files.job.DataImporter;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataToSend;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;

public class DataImporterJob
extends GridJob<Void> {
    private DataImporter dataImporter = new DataImporter();
    private IProgressListener listener;
    private DataInfo dataInfo;
    private ImportDataInfo importInfo;
    private String symbol;

    public DataImporterJob(String symbol, String jobId, IProgressListener listener, DataInfo dataInfo, ImportDataInfo importInfo) {
        super(jobId, 0, null);
        this.listener = listener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
        this.symbol = symbol;
    }

    public Void call() throws Exception {
        try {
            this.listener.setMessage(L.t((String)"Starting file import...", (Object[])new Object[0]));
            this.listener.onProgress(1.0);
            this.dataImporter.performImport(this.listener, this.dataInfo, this.importInfo);
            this.listener.onProgress(100.0);
            this.listener.setMessage(this.dataImporter.isCanceled() ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        }
        catch (Exception e) {
            this.listener.onError(e.getMessage());
        }
        finally {
            this.sendRefreshMessage();
            DataManagerDataProgress.get().removeListener(this.symbol);
        }
        return null;
    }

    private void sendRefreshMessage() {
        try {
            SQWebSocketManager.addToDataQueue((DataToSend)WSDataObjects.getData((String)this.dataInfo.symbol, (String)"import"), (String[])new String[]{"SQUANT", "QDM", "AlgoWizard"});
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

