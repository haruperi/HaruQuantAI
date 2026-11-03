/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.stat;

public class Statistic {
    private long computedTasks = 0L;
    private long resentTasks = 0L;
    private long shortestTaskTime = 0L;
    private long longestTaskTime = 0L;
    private long averageTaskTime = 0L;
    private long totalDuration = 0L;

    public long getComputedTasks() {
        return this.computedTasks;
    }

    public long getResentTasks() {
        return this.resentTasks;
    }

    public long getShortestTaskTime() {
        return this.shortestTaskTime;
    }

    public long getLongestTaskTime() {
        return this.longestTaskTime;
    }

    public long getAverageTaskTime() {
        return this.averageTaskTime;
    }

    public long getTotalDuration() {
        return this.totalDuration;
    }

    public synchronized void taskFailed() {
        ++this.resentTasks;
    }

    public void taskComputed(long l) {
        ++this.computedTasks;
        if (l > this.longestTaskTime) {
            this.longestTaskTime = l;
        }
        if (l < this.shortestTaskTime || this.shortestTaskTime == 0L) {
            this.shortestTaskTime = l;
        }
        this.totalDuration += l;
        this.averageTaskTime = this.totalDuration / this.computedTasks;
    }
}

