/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap
 *  it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap
 *  it.unimi.dsi.fastutil.ints.IntArrayList
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.BadStrategyException;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.project.ComplexDurationStats;
import it.unimi.dsi.fastutil.ints.Int2IntOpenHashMap;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import it.unimi.dsi.fastutil.ints.IntArrayList;
import java.util.HashMap;
import java.util.Map;

public class ProjectRunInfo {
    public static final int ERROR_TYPE_GENERAL = 10;
    public static final int ERROR_TYPE_FATAL = 50;
    public long backtestsPerformed;
    public long strategiesGenerated;
    public long strategiesRejected;
    public double strategiesRejectedPct;
    public long strategiesAccepted;
    public double strategiesAcceptedPct;
    public long timePerStrategy;
    public long timePerAcceptedStrategy;
    public double strategiesPerHour;
    public double acceptedStrategiesPerHour;
    public long strategiesPassed;
    public long strategiesFailed;
    public long startTime;
    public long totalProjectRunningTime;
    public long projectRunningTime;
    public long taskRunningTime;
    public long timeToFinish;
    public int jobExceptionsCount;
    public long totalJobsDone;
    public long runningJobs;
    public long waitingJobs;
    public int totalSteps;
    public int step;
    public boolean infiniteProgress;
    public double progressPercent;
    public String info;
    public String error;
    public String errorInfo;
    public int errorType;
    private Int2IntOpenHashMap dismissalCounts = new Int2IntOpenHashMap();
    private Int2ObjectOpenHashMap<String> dismissalReasons = new Int2ObjectOpenHashMap();
    private Int2IntOpenHashMap acceptedCounts = new Int2IntOpenHashMap();
    private HashMap<String, ComplexDurationStats> complexDurationStats = new HashMap();

    public void copyFrom(ProjectRunInfo projectRunInfo, boolean bl) {
        this.jobExceptionsCount = projectRunInfo.jobExceptionsCount;
        this.totalJobsDone = projectRunInfo.totalJobsDone;
        this.runningJobs = projectRunInfo.runningJobs;
        this.waitingJobs = projectRunInfo.waitingJobs;
        this.taskRunningTime = projectRunInfo.taskRunningTime;
        this.timeToFinish = projectRunInfo.timeToFinish;
        this.backtestsPerformed = projectRunInfo.backtestsPerformed;
        this.strategiesGenerated = projectRunInfo.strategiesGenerated;
        this.strategiesRejected = projectRunInfo.strategiesRejected;
        this.strategiesRejectedPct = projectRunInfo.strategiesRejectedPct;
        this.strategiesAccepted = projectRunInfo.strategiesAccepted;
        this.strategiesAcceptedPct = projectRunInfo.strategiesAcceptedPct;
        this.timePerStrategy = projectRunInfo.timePerStrategy;
        this.timePerAcceptedStrategy = projectRunInfo.timePerAcceptedStrategy;
        this.strategiesPerHour = projectRunInfo.strategiesPerHour;
        this.acceptedStrategiesPerHour = projectRunInfo.acceptedStrategiesPerHour;
        this.strategiesPassed = projectRunInfo.strategiesPassed;
        this.strategiesFailed = projectRunInfo.strategiesFailed;
        this.totalSteps = projectRunInfo.totalSteps;
        this.step = projectRunInfo.step;
        this.infiniteProgress = projectRunInfo.infiniteProgress;
        this.progressPercent = projectRunInfo.progressPercent;
        this.error = projectRunInfo.error;
        this.errorInfo = projectRunInfo.errorInfo;
        this.errorType = projectRunInfo.errorType;
        this.info = projectRunInfo.info;
        if (bl) {
            try {
                this.acceptedCounts.clear();
                this.acceptedCounts.putAll((Map)projectRunInfo.acceptedCounts);
            }
            catch (NullPointerException nullPointerException) {
                // empty catch block
            }
            try {
                this.dismissalCounts.clear();
                this.dismissalCounts.putAll((Map)projectRunInfo.dismissalCounts);
            }
            catch (NullPointerException nullPointerException) {
                // empty catch block
            }
            try {
                this.dismissalReasons.clear();
                this.dismissalReasons.putAll(projectRunInfo.dismissalReasons);
            }
            catch (NullPointerException nullPointerException) {
                // empty catch block
            }
            try {
                this.complexDurationStats.clear();
                this.complexDurationStats.putAll(projectRunInfo.complexDurationStats);
            }
            catch (NullPointerException nullPointerException) {
                // empty catch block
            }
        }
    }

    public void increaseDismissalReasonCount(int n) {
        IntArrayList intArrayList = BadStrategyException.getSubReasons(n);
        for (int i = 0; i < intArrayList.size(); ++i) {
            int n2 = intArrayList.getInt(i);
            if (!this.dismissalCounts.containsKey(n2)) {
                this.dismissalCounts.put(n2, 1);
                continue;
            }
            int n3 = this.dismissalCounts.get(n2);
            this.dismissalCounts.put(n2, n3 + 1);
        }
    }

    public Int2ObjectOpenHashMap<String> getDismissalReasons() {
        return this.dismissalReasons;
    }

    public Int2IntOpenHashMap getDismissalCounts() {
        return this.dismissalCounts;
    }

    public void resetDismissalCounts() {
        this.dismissalCounts.clear();
        this.dismissalReasons.clear();
    }

    public void increaseAcceptedReasonCount(int n) {
        if (!this.acceptedCounts.containsKey(n)) {
            this.acceptedCounts.put(n, 1);
        } else {
            int n2 = this.acceptedCounts.get(n);
            this.acceptedCounts.put(n, n2 + 1);
        }
    }

    public Int2IntOpenHashMap getAcceptedCounts() {
        return this.acceptedCounts;
    }

    public void resetAcceptedCounts() {
        this.acceptedCounts.clear();
    }

    public synchronized void updateDurationStats(DurationStats durationStats) {
        HashMap<String, Double> hashMap = durationStats.getMap();
        if (hashMap == null) {
            return;
        }
        for (String string : hashMap.keySet()) {
            ComplexDurationStats complexDurationStats;
            if (!this.complexDurationStats.containsKey(string)) {
                complexDurationStats = new ComplexDurationStats();
                this.complexDurationStats.put(string, complexDurationStats);
            } else {
                complexDurationStats = this.complexDurationStats.get(string);
            }
            complexDurationStats.update(string, hashMap.get(string));
        }
    }

    public HashMap<String, ComplexDurationStats> getDurationStats() {
        return this.complexDurationStats;
    }

    public void resetDurationStats() {
        this.complexDurationStats.clear();
    }

    public void reset(boolean bl, boolean bl2) {
        this.jobExceptionsCount = 0;
        this.totalJobsDone = 0L;
        this.runningJobs = 0L;
        this.waitingJobs = 0L;
        if (bl2) {
            this.startTime = System.currentTimeMillis();
            this.projectRunningTime = 0L;
            this.totalProjectRunningTime = 0L;
        }
        this.taskRunningTime = 0L;
        this.backtestsPerformed = 0L;
        this.strategiesGenerated = 0L;
        this.strategiesRejected = 0L;
        this.strategiesRejectedPct = 0.0;
        this.strategiesAccepted = 0L;
        this.strategiesAcceptedPct = 0.0;
        this.timePerStrategy = 0L;
        this.timePerAcceptedStrategy = 0L;
        this.strategiesPerHour = 0.0;
        this.acceptedStrategiesPerHour = 0.0;
        this.strategiesPassed = 0L;
        this.strategiesFailed = 0L;
        this.infiniteProgress = bl;
        this.error = null;
        this.errorInfo = null;
        this.errorType = 0;
        this.progressPercent = 0.0;
        this.resetDismissalCounts();
        this.resetAcceptedCounts();
        this.resetDurationStats();
    }
}

