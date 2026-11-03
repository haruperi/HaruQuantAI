/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.dukascopy.job;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadRateCorrector {
    private static final Logger LOGGER = LoggerFactory.getLogger(DownloadRateCorrector.class);
    private volatile int successCount = 0;
    private volatile int failedCount = 0;
    private volatile long downloadDelay = 50L;
    private static final Long MINIMAL_DELAY = 1L;
    private int SUCCESS_COUNT_THREASHOLD = 100;
    private int FAILED_COUNT_THREASHOLD = 1;
    private volatile long lastDownloadTime = 0L;
    private Thread waitingThread;
    private volatile boolean stopped;

    public void downloadFailed() {
        ++this.failedCount;
        if (this.failedCount >= this.FAILED_COUNT_THREASHOLD) {
            long l;
            this.downloadDelay = l = (long)(this.downloadDelay == 0L ? (double)MINIMAL_DELAY.longValue() : (double)this.downloadDelay * 1.25);
            LOGGER.debug("Increasing waiting period to:" + l);
            this.successCount = 0;
            this.failedCount = 0;
        }
    }

    public void downloadSuccess() {
        ++this.successCount;
        if (this.successCount >= this.SUCCESS_COUNT_THREASHOLD) {
            long l;
            this.successCount = 0;
            this.failedCount = 0;
            this.downloadDelay = l = (long)((double)this.downloadDelay * 0.75);
            LOGGER.debug("Decreasing waiting period to:" + l);
        }
    }

    public synchronized void waitBeforeNextDownload() throws InterruptedException {
        if (this.stopped) {
            throw new InterruptedException();
        }
        long l = System.currentTimeMillis() - this.lastDownloadTime;
        long l2 = this.downloadDelay - l;
        if (l2 > 0L) {
            LOGGER.debug("Waiting for:" + l2);
            this.waitingThread = Thread.currentThread();
            Thread.sleep(l2);
            this.waitingThread = null;
        }
        this.lastDownloadTime = System.currentTimeMillis();
    }

    public synchronized void stop() {
        this.stopped = true;
        if (this.waitingThread != null) {
            this.waitingThread.interrupt();
        }
    }
}

