/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.datalib.DataInfo
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.pluginlib.SQPluginManager
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.crypto;

import com.strategyquant.datalib.DataInfo;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.pluginlib.SQPluginManager;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.exchange.IExchange;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import com.strategyquant.tradinglib.project.websocket.SQWebSocketManager;
import com.strategyquant.tradinglib.project.websocket.WSDataObjects;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class CryptoDownloadJob
extends GridJob<Void> {
    public static final Logger Log = LoggerFactory.getLogger(CryptoDownloadJob.class);
    private IExchange downloader;
    private String jobId;
    private DataManagerProgressListener listener;
    private DataInfo dataInfo;
    private ImportInfo importInfo;

    public CryptoDownloadJob(String string, DataManagerProgressListener dataManagerProgressListener, DataInfo dataInfo, ImportInfo importInfo) {
        super(string, 0, null);
        this.jobId = string;
        this.listener = dataManagerProgressListener;
        this.dataInfo = dataInfo;
        this.importInfo = importInfo;
    }

    public Void call() throws Exception {
        try {
            String string = this.dataInfo.uSymbolName;
            IExchange iExchange = this.findExchangeByName(string);
            if (iExchange == null) {
                throw new Exception(L.t((String)"Cannot find plugin for '%s'.", (Object[])new Object[]{string}));
            }
            this.listener.setMessage(L.t((String)"Starting crypto download...", (Object[])new Object[0]));
            this.listener.onProgress(1.0);
            this.downloader = iExchange.clone();
            this.downloader.performDownload(this.jobId, this.listener, this.dataInfo, this.importInfo);
            this.listener.onProgress(100.0);
            this.listener.setMessage(this.downloader.isCanceled() ? L.t((String)"Stopped", (Object[])new Object[0]) : L.t((String)"Completed", (Object[])new Object[0]));
        }
        catch (Exception exception) {
            this.listener.onError(exception.getMessage());
        }
        finally {
            Log.debug("Download job for symbol:" + this.importInfo.symbol + " finished");
        }
        SQWebSocketManager.addToDataQueue(WSDataObjects.getData(this.dataInfo.symbol, "download"), "SQUANT", "QDM", "AlgoWizard");
        return null;
    }

    public void destroy() {
        super.destroy();
        this.listener.onProgress(100.0);
        this.listener.setMessage(L.t((String)"Stopped", (Object[])new Object[0]));
    }

    private IExchange findExchangeByName(String string) {
        for (IExchange iExchange : SQPluginManager.getPlugins(IExchange.class)) {
            if (!iExchange.getName().equals(string)) continue;
            return iExchange;
        }
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

