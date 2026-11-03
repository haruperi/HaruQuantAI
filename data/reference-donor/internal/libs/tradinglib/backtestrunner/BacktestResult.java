/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.backtestrunner;

import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.conditions.DismissStruct;
import java.io.Serializable;

public class BacktestResult
implements Serializable {
    private ResultsGroup resultsGroup;
    private String dismissalMessage = null;
    private int dismissalReason = 0;
    private DurationStats durationStats;
    private int backtestsInJob = 0;

    public BacktestResult(ResultsGroup resultsGroup) {
        this.resultsGroup = resultsGroup;
    }

    public BacktestResult(ResultsGroup resultsGroup, DurationStats durationStats) {
        this.resultsGroup = resultsGroup;
        this.durationStats = durationStats;
    }

    public BacktestResult(String string, int n, DurationStats durationStats) {
        this.dismissalMessage = string;
        this.dismissalReason = n;
        this.durationStats = durationStats;
    }

    public BacktestResult(DismissStruct dismissStruct) {
        this.dismissalMessage = dismissStruct.dismissMessage;
        this.dismissalReason = dismissStruct.dismissReason;
    }

    public BacktestResult dismiss(String string, int n) {
        this.dismissalMessage = string;
        this.dismissalReason = n;
        return this;
    }

    public ResultsGroup getResult() {
        return this.resultsGroup;
    }

    public String getDismissalMessage() {
        return this.dismissalMessage;
    }

    public int getDismissalReason() {
        return this.dismissalReason;
    }

    public boolean isDismissed() {
        return this.dismissalMessage != null;
    }

    public DurationStats getDurationStats() {
        return this.durationStats;
    }

    public int getBacktestsInJob() {
        return this.backtestsInJob;
    }
}

