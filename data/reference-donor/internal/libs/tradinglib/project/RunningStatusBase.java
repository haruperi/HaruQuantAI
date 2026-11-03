/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.project;

import com.strategyquant.tradinglib.project.ProjectStatusListener;
import java.util.concurrent.locks.StampedLock;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RunningStatusBase {
    public static final Logger Log = LoggerFactory.getLogger(RunningStatusBase.class);
    private int runningStatus = 0;
    private StampedLock stampedLock = new StampedLock();
    private ProjectStatusListener listener = null;

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public int getRunningStatus() {
        long l = this.stampedLock.tryOptimisticRead();
        int n = this.runningStatus;
        if (!this.stampedLock.validate(l)) {
            l = this.stampedLock.readLock();
            try {
                n = this.runningStatus;
            }
            finally {
                this.stampedLock.unlockRead(l);
            }
        }
        return n;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void setRunningStatus(int n) {
        long l = this.stampedLock.writeLock();
        try {
            this.runningStatus = n;
            if (this.listener != null) {
                this.listener.projectStatusChanged(n);
            }
        }
        finally {
            this.stampedLock.unlockWrite(l);
        }
    }

    public void setProjectStatusListener(ProjectStatusListener projectStatusListener) {
        this.listener = projectStatusListener;
    }
}

