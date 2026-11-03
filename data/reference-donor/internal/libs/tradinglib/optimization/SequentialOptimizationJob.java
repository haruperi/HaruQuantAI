/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import com.strategyquant.tradinglib.results.SpecialValues;
import java.io.Serializable;
import java.util.Map;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class SequentialOptimizationJob
extends GridJob<BacktestResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"ChainOptimizationJob");
    private BacktestRunner backtestRunner;
    private String note;
    private ILastEventListener lastEventListener;
    private String strategyName;
    private String paramName;
    private double paramValue;

    public SequentialOptimizationJob(String string, Map<String, Serializable> map, StopPauseEngine stopPauseEngine, ILastEventListener iLastEventListener, String string2, String string3, double d, String string4) throws Exception {
        super(string, 1, map);
        this.strategyName = string2;
        this.paramName = string3;
        this.paramValue = d;
        this.lastEventListener = iLastEventListener;
        this.backtestRunner = new BacktestRunner(new BacktestSettings(map), stopPauseEngine, null, false, null, string4);
        try {
            this.note = (String)((Object)map.get("StrategyNote"));
        }
        catch (Exception exception) {
            Log.error("Error while initializing ChainOptimization job", (Throwable)exception);
        }
    }

    public BacktestResult call() throws Exception {
        ResultsGroup resultsGroup;
        Object object;
        if (this.lastEventListener != null) {
            object = L.t((String)"%s: Sequential optimization - %s = %s", (Object[])new Object[]{this.strategyName, this.paramName, "" + this.paramValue});
            this.lastEventListener.setLastEvent((String)object);
        }
        if ((object = this.backtestRunner.execute()) != null && this.note != null && (resultsGroup = ((BacktestResult)object).getResult()) != null) {
            resultsGroup.specialValues().set(SpecialValues.Note, (Object)this.note);
        }
        return object;
    }

    public void messageReceived(GridMessage gridMessage) {
        if (gridMessage.getMessageID() == 4) {
            this.backtestRunner.stop();
        }
    }
}

