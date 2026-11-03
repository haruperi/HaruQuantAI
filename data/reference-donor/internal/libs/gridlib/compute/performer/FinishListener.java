/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.performer;

import com.strategyquant.gridlib.client.Compute;

public class FinishListener {
    private Compute compute;
    private Object object;
    private String waitGroupId;

    public FinishListener(Compute compute, Object object, String string) {
        this.compute = compute;
        this.object = object;
        this.waitGroupId = string;
    }

    public String getWaitGroupId() {
        return this.waitGroupId;
    }

    public boolean isFinished() {
        return this.compute.getWaitingJobsCount(this.waitGroupId) + this.compute.getExecutedUndeliveredJobsCount(this.waitGroupId) == 0L;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void notifyWaitingObj() {
        try {
            Object object = this.object;
            synchronized (object) {
                this.object.notify();
            }
        }
        catch (IllegalMonitorStateException illegalMonitorStateException) {
            illegalMonitorStateException.printStackTrace();
        }
    }
}

