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
package com.strategyquant.tradinglib.dukascopy;

import com.strategyquant.gridlib.client.GridClient;
import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.gridlib.client.IGridMessageListener;
import com.strategyquant.gridlib.client.SQGrid;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.dukascopy.ImportInfo;
import com.strategyquant.tradinglib.dukascopy.job.DownloadDukascopySymbolJob;
import com.strategyquant.tradinglib.project.websocket.DataManagerDataProgress;
import com.strategyquant.tradinglib.project.websocket.DataManagerProgressListener;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.locks.ReentrantLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DukasImportManager {
    private static final String IMPORT_FILE_DUKASCOPY_JOB = "ImportFileDukascopyJob_";
    public static final String DOWNLOAD_DUKASCOPY_SYMBOL_JOB = "DownloadDukascopySymbolJob_";
    public static final Logger Log = LoggerFactory.getLogger(DukasImportManager.class);
    private Map<String, DownloadDukascopySymbolJob> downloadJobs = new HashMap<String, DownloadDukascopySymbolJob>();
    private static ReentrantLock lock = new ReentrantLock();
    private static DukasImportManager instance;

    public static synchronized DukasImportManager get() {
        if (instance == null) {
            try {
                lock.lock();
                if (instance == null) {
                    instance = new DukasImportManager();
                }
            }
            finally {
                lock.unlock();
            }
        }
        return instance;
    }

    private DukasImportManager() {
        this.prepareDukasDownloadListener();
    }

    private void prepareDukasDownloadListener() {
        SQGrid.getGridClient().registerMessageListener("DukascopyDownloadPerformerGroup", new IGridMessageListener(){

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
                    DownloadDukascopySymbolJob downloadDukascopySymbolJob = null;
                    try {
                        lock.lock();
                        downloadDukascopySymbolJob = (DownloadDukascopySymbolJob)((Object)DukasImportManager.this.downloadJobs.get(string2));
                    }
                    finally {
                        lock.unlock();
                    }
                    if (downloadDukascopySymbolJob == null) {
                        return;
                    }
                    downloadDukascopySymbolJob.handleDownloadedMessage(gridMessage);
                }
            }
        });
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public GridJob importData(final String string, String string2, ImportInfo importInfo, DataManagerProgressListener dataManagerProgressListener, final IGridMessageListener iGridMessageListener) {
        if (SQGrid.getGridClient().countRunningJobs(IMPORT_FILE_DUKASCOPY_JOB + importInfo.symbol) != 0L) {
            throw new RuntimeException(L.t((String)"Import from TickDownloader is already running.", (Object[])new Object[0]));
        }
        final GridClient gridClient = SQGrid.getGridClient();
        if (gridClient.isRegisteredMessageListener(string)) {
            throw new RuntimeException(L.t((String)"Downloading of symbol '%s' is already running.", (Object[])new Object[]{importInfo.symbol}));
        }
        DataManagerDataProgress.get().setProgress(importInfo.symbol, 0, L.t((String)"Waiting...", (Object[])new Object[0]));
        try {
            gridClient.registerMessageListener(string, new IGridMessageListener(){
                final /* synthetic */ DukasImportManager this$0;
                {
                    this.this$0 = dukasImportManager;
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
            DownloadDukascopySymbolJob downloadDukascopySymbolJob = new DownloadDukascopySymbolJob(string2, string, importInfo);
            downloadDukascopySymbolJob.setProgressListener(dataManagerProgressListener);
            try {
                lock.lock();
                this.downloadJobs.put(string, downloadDukascopySymbolJob);
            }
            finally {
                lock.unlock();
            }
            return downloadDukascopySymbolJob;
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

