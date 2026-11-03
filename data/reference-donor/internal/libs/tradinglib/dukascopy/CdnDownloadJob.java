/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 */
package com.strategyquant.tradinglib.dukascopy;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.tradinglib.dukascopy.CdnCache;
import com.strategyquant.tradinglib.dukascopy.DownloadResultDto;
import com.strategyquant.tradinglib.historyData.DownloadMessageHandler;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class CdnDownloadJob
extends GridJob<DownloadResultDto> {
    private static final long serialVersionUID = 1L;
    private CdnCache cache;
    private int year;
    private int month;
    private int day;
    private DownloadMessageHandler failedHandler;
    private Future<DownloadResultDto> downloadFuture;
    private final ExecutorService executor = Executors.newSingleThreadExecutor();

    public CdnDownloadJob(String string, CdnCache cdnCache, int n, int n2, int n3, int n4, DownloadMessageHandler downloadMessageHandler) {
        super(string, n4, null);
        this.cache = cdnCache;
        this.year = n;
        this.month = n2;
        this.day = n3;
        this.failedHandler = downloadMessageHandler;
    }

    public DownloadResultDto call() throws Exception {
        try {
            this.downloadFuture = this.executor.submit(() -> this.cache.performLoad(this.year, this.month, this.day, this.failedHandler));
            DownloadResultDto downloadResultDto = this.downloadFuture.get();
            return downloadResultDto;
        }
        catch (CancellationException cancellationException) {
            return null;
        }
    }

    public void messageReceived(GridMessage gridMessage) {
        super.messageReceived(gridMessage);
        if (gridMessage.getMessageID() == 4) {
            this.cache.stop();
            this.downloadFuture.cancel(true);
        }
    }
}

