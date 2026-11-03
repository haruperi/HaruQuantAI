/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.datalib.data;

import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DownloadSemaphore {
    private static final Logger Log = LoggerFactory.getLogger(DownloadSemaphore.class);
    private Semaphore semaphore = new Semaphore(1);
    private static final DownloadSemaphore instance = new DownloadSemaphore();

    public static DownloadSemaphore getInstance() {
        return instance;
    }

    public boolean startDownloadData(int n) throws InterruptedException {
        Log.info("Acquiring semaphore");
        boolean bl = this.semaphore.tryAcquire(n, TimeUnit.SECONDS);
        Log.info("Semaphore acquired with result: {}", (Object)bl);
        return bl;
    }

    public void downloadFinished() {
        this.semaphore.release();
        Log.info("Semaphore released");
    }
}

