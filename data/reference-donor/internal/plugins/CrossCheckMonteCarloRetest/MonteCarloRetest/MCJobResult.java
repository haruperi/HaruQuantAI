/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.backtestrunner.DurationStats
 *  com.strategyquant.tradinglib.robustnesstests.RobustnessResults
 */
package com.strategyquant.plugin.CrossCheck.impl.MonteCarloRetest;

import com.strategyquant.tradinglib.backtestrunner.DurationStats;
import com.strategyquant.tradinglib.robustnesstests.RobustnessResults;
import java.io.Serializable;

public class MCJobResult
implements Serializable {
    private RobustnessResults rr;
    private Object durationStats;
    private String dismissalMessage;
    private int dismissalReason;

    public MCJobResult(RobustnessResults rr, DurationStats durationStats) {
        this.rr = rr;
        this.durationStats = durationStats;
    }

    public MCJobResult(String dismissalMessage, int dismissalReason, DurationStats durationStats) {
        this.dismissalMessage = dismissalMessage;
        this.dismissalReason = dismissalReason;
        this.durationStats = durationStats;
    }

    public RobustnessResults getRR() {
        return this.rr;
    }

    public String getDismissalMessage() {
        return this.dismissalMessage;
    }
}

