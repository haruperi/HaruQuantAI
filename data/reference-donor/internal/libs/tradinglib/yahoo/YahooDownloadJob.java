/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.yahoo;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import com.strategyquant.tradinglib.yahoo.YahooDownloader;

public class YahooDownloadJob
extends GridJob<Void> {
    private YahooDownloader downloader = new YahooDownloader();
    private String jobId;
    private DataManagerProgressListener listener;
    private DataInfo dataInfo;
    private ImportInfo importInfo;

    public YahooDownloadJob(String string, DataManagerProgressListener dataManagerProgressListener, DataInfo dataInfo, ImportInfo importInfo) {
        super(string, 0, null);
        this.jobId = string;
        this.listener = dataManagerProgressListener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
    }

    public Void call() throws Exception {
        try {
            this.listener.setMessage(L.t((String)"Starting Yahoo download...", (Object[])new Object[]{true}));
            this.listener.onProgress(1.0);
            this.downloader.performDownload(this.jobId, this.listener, this.dataInfo, this.importInfo);
            this.listener.onProgress(100.0);
            this.listener.setMessage(this.downloader.isCanceled() ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        }
        catch (Exception exception) {
            this.listener.onError(exception.getMessage());
        }
        SQWebSocketManager.addToDataQueue(WSDataObjects.getData(this.dataInfo.symbol, "download"), "SQUANT", "QDM", "AlgoWizard");
        return null;
    }

    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        switch (gridMessage.getMessageID()) {
            case 4: {
                this.downloader.cancel();
                break;
            }
            case 2: {
                this.downloader.pause();
                break;
            }
            case 3: {
                this.downloader.restart();
            }
        }
    }
}

