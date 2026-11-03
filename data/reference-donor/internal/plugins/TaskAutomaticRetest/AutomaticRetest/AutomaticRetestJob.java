/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.gridlib.client.GridMessage
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SettingsMap
 *  com.strategyquant.lib.XMLUtil
 *  com.strategyquant.tradinglib.Databank
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtest.BacktestDataInitializer
 *  com.strategyquant.tradinglib.backtest.LoadDataProgressEngine
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.backtestrunner.BacktestRunner
 *  com.strategyquant.tradinglib.backtestrunner.BacktestSettings
 *  com.strategyquant.tradinglib.project.ILastEventListener
 *  com.strategyquant.tradinglib.project.ProjectEngine
 *  com.strategyquant.tradinglib.project.SQProject
 *  com.strategyquant.tradinglib.project.StopPauseEngine
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticRetest;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.gridlib.client.GridMessage;
import com.strategyquant.lib.L;
import com.strategyquant.lib.SettingsMap;
import com.strategyquant.lib.XMLUtil;
import com.strategyquant.tradinglib.Databank;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtest.BacktestDataInitializer;
import com.strategyquant.tradinglib.backtest.LoadDataProgressEngine;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectEngine;
import com.strategyquant.tradinglib.project.SQProject;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.io.Serializable;
import java.util.ArrayList;
import java.util.Map;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class AutomaticRetestJob
extends GridJob<BacktestResult> {
    public static final Logger Log = LoggerFactory.getLogger((String)"RetestJob");
    private BacktestRunner backtestRunner;
    private SQProject project;
    private String strategyName;
    private Map<String, Serializable> params;

    public AutomaticRetestJob(String jobID, Map<String, Serializable> params, StopPauseEngine stopPauseEngine, ILastEventListener lastEventListener) throws Exception {
        super(jobID, 1, params);
        this.params = params;
        this.backtestRunner = new BacktestRunner(new BacktestSettings(params), stopPauseEngine, (GridJob)this, true, lastEventListener, XMLUtil.xmlToString((Element)((Element)params.get("StrategyLastSettings"))));
        try {
            this.strategyName = (String)((Object)params.get("StrategyName"));
            Databank srcDatabank = (Databank)params.get("DatabankSource");
            this.project = ProjectEngine.get((String)srcDatabank.getProject());
        }
        catch (Exception exception) {
            // empty catch block
        }
    }

    private void initializeBacktestData(Map<String, Serializable> params) throws Exception {
        ArrayList chartSetups = (ArrayList)params.get("ChartSetups");
        boolean useCrossChecks = SettingsMap.getBool((Object)params.get("UseRobustnessTests"), (boolean)false);
        ArrayList crossChecks = (ArrayList)params.get("CrossChecks");
        BacktestDataInitializer bdi = new BacktestDataInitializer(new LoadDataProgressEngine(this.project.progressEngine), chartSetups, useCrossChecks, crossChecks);
        bdi.prepareData();
    }

    public BacktestResult call() throws Exception {
        try {
            this.initializeBacktestData(this.params);
            BacktestResult result = this.backtestRunner.execute();
            try {
                ResultsGroup rg = result.getResult();
                rg.setLastSettings(XMLUtil.xmlToString((Element)((Element)this.params.get("StrategyLastSettings"))));
            }
            catch (Exception exception) {
                // empty catch block
            }
            return result;
        }
        catch (Exception e) {
            if (this.project != null) {
                this.project.printToLog(L.t((String)"Automatic Backtest of '%s' failed - %s", (Object[])new Object[]{this.strategyName, e.getMessage()}));
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

