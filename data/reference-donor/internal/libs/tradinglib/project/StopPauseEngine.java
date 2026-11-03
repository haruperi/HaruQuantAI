/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.RunningStatus
 *  com.strategyquant.lib.IStopPauseStatus
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.time.SQTimeOld
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.gridlib.client.RunningStatus;
import com.strategyquant.lib.IStopPauseStatus;
import com.strategyquant.lib.L;
import com.strategyquant.lib.time.SQTimeOld;
import com.strategyquant.tradinglib.project.IProgressStatusListener;
import com.strategyquant.tradinglib.project.RunningStatusBase;
import java.util.concurrent.ConcurrentLinkedQueue;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class StopPauseEngine
extends RunningStatusBase
implements IStopPauseStatus {
    public static final Logger Log = LoggerFactory.getLogger(StopPauseEngine.class);
    private long startTime;
    private long elapsedTime;
    private ConcurrentLinkedQueue<IProgressStatusListener> listeners = new ConcurrentLinkedQueue();

    public void start() throws Exception {
        int n = this.getRunningStatus();
        if (!RunningStatus.canBeStarted((int)n)) {
            Log.info("Cannot start project in incorrect running status: {}", (Object)n);
            return;
        }
        this.startTime = System.currentTimeMillis();
        this.elapsedTime = 0L;
        this.setStatus(1);
    }

    public void pause() {
        int n = this.getRunningStatus();
        if (n == 1) {
            this.printToLog(L.t((String)"Project paused", (Object[])new Object[0]));
            this.setStatus(2);
        }
    }

    public void resume() {
        int n = this.getRunningStatus();
        if (n == 2) {
            this.printToLog(L.t((String)"Project resumed", (Object[])new Object[0]));
            this.setStatus(1);
        }
    }

    public void stop() {
        this.stop(true);
    }

    public void stop(boolean bl) {
        int n = this.getRunningStatus();
        if (n == 1 || n == 2) {
            if (bl) {
                this.printToLog(L.t((String)"Project stopped", (Object[])new Object[0]));
            }
            this.setStatus(4);
        }
    }

    public void finish() {
        int n = this.getRunningStatus();
        if (n == 1 || n == 2) {
            this.setStatus(3);
        }
    }

    protected void setStatus(int n) {
        this.setRunningStatus(n);
        for (IProgressStatusListener iProgressStatusListener : this.listeners) {
            iProgressStatusListener.onStatusChanged(n);
        }
    }

    public void registerStatusListener(IProgressStatusListener iProgressStatusListener) {
        if (!this.listeners.contains(iProgressStatusListener)) {
            this.listeners.add(iProgressStatusListener);
        }
    }

    public void unregisterStatusListener(IProgressStatusListener iProgressStatusListener) {
        this.listeners.remove(iProgressStatusListener);
    }

    public void done() {
        this.elapsedTime = System.currentTimeMillis() - this.startTime;
        String string = SQTimeOld.formatDateTime((long)((int)(this.elapsedTime / 1000L)));
        this.printToLog(L.t((String)"Finished in %s", (Object[])new Object[]{string}));
    }

    public boolean isStopped() {
        int n = this.getRunningStatus();
        return n == 4 || n == 3 || n == 50;
    }

    public boolean isStoppedNotFinished() {
        int n = this.getRunningStatus();
        return n == 4 || n == 50;
    }

    public boolean isPaused() {
        int n = this.getRunningStatus();
        return n == 2;
    }

    public boolean isFinished() {
        int n = this.getRunningStatus();
        return n == 3;
    }

    public boolean checkRunning() {
        int n = this.getRunningStatus();
        return n == 1;
    }

    public void checkPaused() {
        if (!this.isPaused()) {
            return;
        }
        while (this.isPaused()) {
            try {
                Thread.sleep(100L);
            }
            catch (InterruptedException interruptedException) {
                interruptedException.printStackTrace();
            }
        }
    }

    public void printToLog(String string) {
    }

    public void printToLogDebug(String string) {
    }

    public void reset() {
        this.setRunningStatus(0);
    }

    public void error() {
        this.setStatus(50);
    }
}

