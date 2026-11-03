/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.backtestrunner.BacktestRunner
 *  com.strategyquant.tradinglib.backtestrunner.BacktestSettings
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  com.strategyquant.tradinglib.results.SpecialValues
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.Retest;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.io.Serializable;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RetestJob
extends GridJob<BacktestResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"RetestJob");
    private BacktestRunner backtestRunner;
    private SQProject project;
    private String strategyName;
    private String note;

    public RetestJob(String jobID, Map<String, Serializable> params, StopPauseEngine stopPauseEngine, ILastEventListener lastEventListener, String lastSettingsXml) throws Exception {
        super(jobID, 1, params);
        this.backtestRunner = new BacktestRunner(new BacktestSettings(params), stopPauseEngine, (GridJob)this, true, lastEventListener, lastSettingsXml);
        try {
            this.strategyName = (String)((Object)params.get("StrategyName"));
            this.note = (String)((Object)params.get("StrategyNote"));
            Databank srcDatabank = (Databank)params.get("DatabankSource");
            this.project = ProjectEngine.get((String)srcDatabank.getProject());
        }
        catch (Exception e) {
            Log.error("Error while initializing Retest job", (Throwable)e);
        }
    }

    public BacktestResult call() throws Exception {
        try {
            ResultsGroup rg;
            BacktestResult result = this.backtestRunner.execute();
            if (result != null && this.note != null && (rg = result.getResult()) != null) {
                rg.specialValues().set(SpecialValues.Note, (Object)this.note);
            }
            return result;
        }
        catch (Exception e) {
            if (this.project != null) {
                this.project.printToLog(L.t((String)"Backtest of '%s' failed - %s", (Object[])new Object[]{this.strategyName, e.getMessage()}));
            }
            throw e;
        }
    }

    public void messageReceived(GridMessage message) {
        if (message.getMessageID() == 4) {
            this.backtestRunner.stop();
        }
    }
}

