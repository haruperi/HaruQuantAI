/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridClient
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.gridlib.client.IGridMessageListener
 *  com.strategyquant.gridlib.client.SQGrid
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.darwinex;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.darwinex.DarwinexDownloadJob;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DarwinexImportManager {
    public static final Logger Log = LoggerFactory.getLogger(DarwinexImportManager.class);
    private Map<String, DarwinexDownloadJob> downloadJobs = new HashMap<String, DarwinexDownloadJob>();
    private static ReentrantLock lock = new ReentrantLock();
    private static DarwinexImportManager instance;

    public static synchronized DarwinexImportManager get() {
        if (instance == null) {
            try {
                lock.lock();
                if (instance == null) {
                    instance = new DarwinexImportManager();
                }
            }
            finally {
                lock.unlock();
            }
        }
        return instance;
    }

    private DarwinexImportManager() {
        this.prepareDownloadListener();
    }

    private void prepareDownloadListener() {
        SQGrid.getGridClient().registerMessageListener("DarwinexDownloadPerformerGroup", new IGridMessageListener(){

            /*
             * WARNING - Removed try catching itself - possible behaviour change.
             */
            public void messageReceived(GridMessage gridMessage) {
                if (gridMessage.getMessageID() == 1) {
                    String string = gridMessage.getJobDetails().getJobID();
                    if (string.endsWith("cdn")) {
                        string = string.substring(0, string.length() - 4);
                    }
                    int n = string.lastIndexOf("_");
                    String string2 = string.substring(0, n);
                    DarwinexDownloadJob darwinexDownloadJob = null;
                    try {
                        lock.lock();
                        darwinexDownloadJob = (DarwinexDownloadJob)((Object)DarwinexImportManager.this.downloadJobs.get(string2));
                    }
                    finally {
                        lock.unlock();
                    }
                    if (darwinexDownloadJob == null) {
                        return;
                    }
                    darwinexDownloadJob.handleDownloadedMessage(gridMessage);
                }
            }
        });
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public GridJob importData(final String string, String string2, ImportInfo importInfo, DataManagerProgressListener dataManagerProgressListener, final IGridMessageListener iGridMessageListener) {
        final GridClient gridClient = SQGrid.getGridClient();
        if (gridClient.isRegisteredMessageListener(string)) {
            throw new RuntimeException(L.t((String)"Downloading of symbol %s is already running.", (Object[])new Object[]{importInfo.symbol}));
        }
        DataManagerDataProgress.get().setProgress(importInfo.symbol, 0, L.t((String)"Waiting...", (Object[])new Object[0]));
        try {
            gridClient.registerMessageListener(string, new IGridMessageListener(){
                final /* synthetic */ DarwinexImportManager this$0;
                {
                    this.this$0 = darwinexImportManager;
                }

                public void messageReceived(GridMessage gridMessage) {
                    if (gridMessage.getMessageID() == 1) {
                        try {
                            lock.lock();
                            gridClient.removeMessageListener(string);
                            this.this$0.downloadJobs.remove(string);
                        }
                        finally {
                            lock.unlock();
                        }
                        if (iGridMessageListener != null) {
                            iGridMessageListener.messageReceived(gridMessage);
                        }
                    }
                }
            });
            DarwinexDownloadJob darwinexDownloadJob = new DarwinexDownloadJob(string2, string, importInfo);
            darwinexDownloadJob.setProgressListener(dataManagerProgressListener);
            try {
                lock.lock();
                this.downloadJobs.put(string, darwinexDownloadJob);
            }
            finally {
                lock.unlock();
            }
            return darwinexDownloadJob;
        }
        catch (Exception exception) {
            Log.error("", (Throwable)exception);
            if (dataManagerProgressListener != null) {
                dataManagerProgressListener.onError("Error - " + exception.getMessage());
            }
            throw new RuntimeException(exception);
        }
    }
}

