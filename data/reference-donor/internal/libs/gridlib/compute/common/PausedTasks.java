/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.compute.common;

import com.strategyquant.gridlib.compute.common.JobQueue;
import java.io.Serializable;
import java.util.List;

public class PausedTasks<T extends Serializable> {
    private List<JobQueue.JobInfo<T>> resultWaiting;
    private List<JobQueue.JobInfo<T>> resultRunning;

    public PausedTasks(List<JobQueue.JobInfo<T>> list, List<JobQueue.JobInfo<T>> list2) {
        this.resultWaiting = list;
        this.resultRunning = list2;
    }

    public List<JobQueue.JobInfo<T>> getRunningTasks() {
        return this.resultRunning;
    }
}

