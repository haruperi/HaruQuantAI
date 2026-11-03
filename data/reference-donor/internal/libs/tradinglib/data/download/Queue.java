/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.data.download;

import com.strategyquant.tradinglib.data.download.DownloadDispatcher;
import com.strategyquant.tradinglib.data.download.IDownloadDispatcher;
import java.util.HashSet;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class Queue {
    private static final Logger Log = LoggerFactory.getLogger(Queue.class);
    private int queueSize = 3;
    private Set<String> executedJobs = new HashSet<String>();
    private LinkedHashMap<String, DownloadDispatcher.Details> downloadQueue = new LinkedHashMap();
    private IDownloadDispatcher dispatcher;

    public Queue(IDownloadDispatcher iDownloadDispatcher) {
        this.dispatcher = iDownloadDispatcher;
    }

    public synchronized void register(String string, DownloadDispatcher.Details details) {
        this.downloadQueue.put(string, details);
    }

    public synchronized DownloadDispatcher.Details removeFromDownloadQueue(String string) {
        return (DownloadDispatcher.Details)this.downloadQueue.remove(string);
    }

    public synchronized DownloadDispatcher.Details getFromDownloadQueue(String string) {
        return this.downloadQueue.get(string);
    }

    public boolean setQueueSize(int n) {
        boolean bl = n > this.queueSize;
        this.queueSize = n;
        return bl;
    }

    public synchronized int getJobsCount() {
        return this.executedJobs.size() + this.downloadQueue.size();
    }

    public synchronized int getRunningJobsCount() {
        return this.executedJobs.size();
    }

    public synchronized int getWaitingJobsCount() {
        return this.downloadQueue.size();
    }

    public boolean exists(String string) {
        return this.downloadQueue.containsKey(string) || this.executedJobs.contains(string);
    }

    public synchronized void tryToRunDownload() {
        Log.debug("Trying to execute next download. Current downloading size: " + this.executedJobs.size());
        if (this.executedJobs.size() < this.queueSize) {
            Iterator<Map.Entry<String, DownloadDispatcher.Details>> iterator = this.downloadQueue.entrySet().iterator();
            while (iterator.hasNext()) {
                Map.Entry<String, DownloadDispatcher.Details> entry = iterator.next();
                if (entry.getValue().paused) continue;
                DownloadDispatcher.Details details = entry.getValue();
                if (details.dataInfo.source == 7 && this.dispatcher.isCryptoExchangeDownload(details.dataInfo.uSymbolName)) {
                    Log.debug("Skipping crypto symbol, because the same exchange is already downloading. " + details.symbol);
                    continue;
                }
                if (details.dataInfo.source == 8 && this.dispatcher.isMt5DownloadExecuted()) {
                    Log.debug("Skipping mt5api symbol, because another symbol is already downloading. " + details.symbol);
                    continue;
                }
                iterator.remove();
                try {
                    this.dispatcher.extecuteDownloadJob(details);
                    this.executedJobs.add(details.symbol);
                }
                catch (Exception exception) {
                    details.listener.onError("Error while executing download job: " + exception.getMessage());
                    Log.error("", (Throwable)exception);
                }
                Log.debug("Executed symbol: " + details.symbol + ", executed: " + this.executedJobs.size());
                if (this.executedJobs.size() < this.queueSize) continue;
                return;
            }
        }
    }

    public int getQueueSize() {
        return this.queueSize;
    }

    public synchronized void stopAll() {
        for (DownloadDispatcher.Details object : this.downloadQueue.values()) {
            this.dispatcher.performStop(object.symbol, object);
        }
        this.downloadQueue.clear();
        for (String string : this.executedJobs) {
            this.dispatcher.performStop(string, null);
        }
        this.executedJobs.clear();
    }

    public synchronized void pauseAll() {
        for (DownloadDispatcher.Details object : this.downloadQueue.values()) {
            this.dispatcher.performPause(object.symbol, object);
        }
        Log.info("Paused waiting jobs");
        for (String string : this.executedJobs) {
            this.dispatcher.performPause(string, null);
        }
        Log.info("Paused running jobs");
    }

    public synchronized void resumeAll() {
        for (DownloadDispatcher.Details object : this.downloadQueue.values()) {
            this.dispatcher.performResume(object.symbol, object);
        }
        Log.info("Resumed waiting jobs");
        for (String string : this.executedJobs) {
            this.dispatcher.performResume(string, null);
        }
        Log.info("Resumed executed jobs");
    }

    public synchronized boolean downloadJobFinished(String string) {
        return this.executedJobs.remove(string);
    }

    public synchronized boolean isBusy() {
        return !this.executedJobs.isEmpty() || !this.downloadQueue.isEmpty();
    }
}

