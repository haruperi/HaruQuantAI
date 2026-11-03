/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.gridlib.stat;

import com.strategyquant.gridlib.stat.Statistic;
import java.util.HashMap;
import java.util.Map;

public class ComputingStats {
    private long computedTasks = 0L;
    private long resentTasks = 0L;
    private Map<String, Statistic> groupStats = new HashMap<String, Statistic>();
    private Map<String, Statistic> nodeStats = new HashMap<String, Statistic>();

    public long getComputedTasks() {
        return this.computedTasks;
    }

    public long getResentTasks() {
        return this.resentTasks;
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Statistic getStatisticForNode(String string) {
        Map<String, Statistic> map = this.nodeStats;
        synchronized (map) {
            Statistic statistic = this.nodeStats.get(string);
            if (statistic == null) {
                statistic = new Statistic();
                this.nodeStats.put(string, statistic);
            }
            return statistic;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public Statistic getStatisticForGroup(String string) {
        Map<String, Statistic> map = this.groupStats;
        synchronized (map) {
            Statistic statistic = this.groupStats.get(string);
            if (statistic == null) {
                statistic = new Statistic();
                this.groupStats.put(string, statistic);
            }
            return statistic;
        }
    }

    /*
     * WARNING - Removed try catching itself - possible behaviour change.
     */
    public void removeStatisticsForNode(String string) {
        Map<String, Statistic> map = this.nodeStats;
        synchronized (map) {
            this.nodeStats.remove(string);
        }
    }

    public void jobComputed(String string, String string2, long l) {
        this.getStatisticForGroup(string).taskComputed(l);
        this.getStatisticForNode(string2).taskComputed(l);
        ++this.computedTasks;
    }

    public void jobFailed(String string, String string2) {
        this.getStatisticForGroup(string).taskFailed();
        this.getStatisticForNode(string2).taskFailed();
        ++this.resentTasks;
    }
}

