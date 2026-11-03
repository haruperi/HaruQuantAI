/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 */
package com.strategyquant.jobslib.databank;

import com.strategyquant.jobslib.SQJob;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;

public class AddToDatabankJob
extends SQJob {
    private ResultsGroup resultsGroup;
    private Databank databank;

    public AddToDatabankJob(ResultsGroup resultsGroup, Databank databank) {
        this.resultsGroup = resultsGroup;
        this.databank = databank;
    }

    @Override
    public void run() throws Exception {
        ResultsGroup resultsGroup = this.resultsGroup.clone();
        this.databank.add(resultsGroup, true);
        this.databank.updateBestResults(resultsGroup);
    }
}

