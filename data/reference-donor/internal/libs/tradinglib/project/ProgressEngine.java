/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.databank.IProgressListener;
import com.strategyquant.tradinglib.project.SQLogger;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.ArrayList;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class ProgressEngine
extends StopPauseEngine {
    public static final Logger Log = LoggerFactory.getLogger(ProgressEngine.class);
    private String projectName;
    private String taskName;
    protected long progress = 0L;
    protected long maxProgress;
    private ArrayList<IProgressListener> listeners = new ArrayList();
    private String logPrefix = null;
    private int previousMessageHash = 0;
    StampedLock stampedLock = new StampedLock();

    public ProgressEngine(String string) {
        this.projectName = string;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void printToLogDebug(String string) {
        if (string == null) {
            return;
        }
        long l = this.stampedLock.writeLock();
        try {
            if (this.logPrefix != null) {
                string = this.logPrefix + " : " + string;
            }
            if (string.hashCode() != this.previousMessageHash) {
                Log.debug(string);
                SQLogger.log(this.projectName, string);
                this.previousMessageHash = string.hashCode();
            }
        }
        finally {
            this.stampedLock.unlockWrite(l);
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    @Override
    public void printToLog(String string) {
        if (string == null) {
            return;
        }
        long l = this.stampedLock.writeLock();
        try {
            if (this.logPrefix != null) {
                string = this.logPrefix + " : " + string;
            }
            if (string.hashCode() != this.previousMessageHash) {
                Log.info(string);
                SQLogger.log(this.projectName, string);
                this.previousMessageHash = string.hashCode();
            }
        }
        finally {
            this.stampedLock.unlockWrite(l);
        }
    }

    public void reset(String string, long l) {
        this.taskName = string;
        this.maxProgress = l;
        this.setProgress(0L);
    }

    public void setProgress(long l) {
        this.progress = l;
        for (int i = 0; i < this.listeners.size(); ++i) {
            this.listeners.get(i).onProgress(l);
        }
    }

    public double getMaxProgress() {
        return this.maxProgress;
    }

    public void setLogPrefix(String string) {
        this.logPrefix = string;
    }

    @Override
    public void finish() {
        this.finish(0L);
    }

    public void finish(long l) {
        int n = this.getRunningStatus();
        if (n == 1 || n == 2 || n == 2) {
            this.setStatus(3);
            String string = this.logPrefix == null ? L.t((String)"Project finished", (Object[])new Object[0]) : L.t((String)"Task finished", (Object[])new Object[0]);
            if (l != 0L) {
                string = string + String.format(" in %.2f s.", (double)l / 1000.0);
            }
            this.printToLog(string);
        }
    }

    public void registerProgressListener(IProgressListener iProgressListener) {
        if (!this.listeners.contains(iProgressListener)) {
            this.listeners.add(iProgressListener);
        }
    }

    public String getLogPrefix() {
        return this.logPrefix;
    }

    public void setProjectName(String string) {
        this.projectName = string;
    }
}

