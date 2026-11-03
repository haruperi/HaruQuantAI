/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.gridlib.client.GridJob
 *  com.strategyquant.lib.SQUtils
 *  com.strategyquant.lib.TaskStoppedException
 *  org.jdom2.Element
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp.strategies;

import com.strategyquant.gridlib.client.GridJob;
import com.strategyquant.lib.SQUtils;
import com.strategyquant.lib.TaskStoppedException;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.backtestrunner.BacktestRunner;
import com.strategyquant.tradinglib.backtestrunner.BacktestSettings;
import com.strategyquant.tradinglib.crosscheck.ICrossCheck;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IFitnessEvaluator;
import com.strategyquant.tradinglib.gp.strategies.Node;
import com.strategyquant.tradinglib.project.ILastEventListener;
import com.strategyquant.tradinglib.project.ProjectConfigHelper;
import com.strategyquant.tradinglib.project.StopPauseEngine;
import java.util.ArrayList;
import org.jdom2.Element;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class BacktestEvaluator
implements IFitnessEvaluator<Node> {
    private static final Logger Log = LoggerFactory.getLogger((String)"BacktestEvaluator");
    private BacktestSettings backtestSettings;
    private BacktestRunner backtestRunner;
    private ILastEventListener lastEventListener;
    private final String lastSettingsXml;

    public BacktestEvaluator(BacktestSettings backtestSettings, ILastEventListener iLastEventListener, String string) {
        this.backtestSettings = backtestSettings;
        this.lastEventListener = iLastEventListener;
        this.lastSettingsXml = string;
    }

    @Override
    public Node evaluateCandidate(Node node, int n, GridJob gridJob, boolean bl) {
        Element element = null;
        try {
            ResultsGroup resultsGroup;
            GPIDs gPIDs = node.getGPIDs();
            if (bl) {
                // empty if block
            }
            this.backtestSettings.strategyName = this.getStrategyName(gPIDs);
            StopPauseEngine stopPauseEngine = new StopPauseEngine();
            stopPauseEngine.start();
            this.backtestRunner = new BacktestRunner(this.backtestSettings, stopPauseEngine, gridJob, false, this.lastEventListener, this.lastSettingsXml);
            String string = String.format("Strategy %d.%d.%d", gPIDs.islandIndex + 1, gPIDs.generationIndex, gPIDs.nodeIndex);
            if (Log.isDebugEnabled()) {
                Log.debug("--- Job {} started", (Object)string);
            }
            element = node.getStrategy();
            this.backtestRunner.setStrategyName(string);
            this.backtestRunner.setStrategy(element);
            this.backtestRunner.setEvolution(true);
            BacktestResult backtestResult = this.backtestRunner.execute(n);
            int n2 = backtestResult.getDismissalReason();
            String string2 = backtestResult.getDismissalMessage();
            node.setDurationStats(backtestResult.getDurationStats());
            if (string2 != null) {
                node.setError(n2, string2, null);
            }
            if ((resultsGroup = backtestResult.getResult()) == null) {
                if (string2 == null) {
                    node.setError(10001, "No dismissal message, but ResultsGroup was null in BacktestResult", null);
                }
            } else {
                node.setFitness(resultsGroup.portfolio().getFitness((byte)10), (byte)10);
                node.setFitness(resultsGroup.portfolio().getFitness((byte)11), (byte)11);
                node.setFitness(resultsGroup.portfolio().getFitness((byte)40), (byte)40);
                node.setFitness(resultsGroup.portfolio().getFitness((byte)20), (byte)20);
                node.setResultsGroup(resultsGroup);
            }
            return node;
        }
        catch (Exception exception) {
            if (exception instanceof TaskStoppedException) {
                Log.info("Task stopped.");
            } else if (!exception.getMessage().contains("Invalid output index:")) {
                Log.error(SQUtils.getStackTrace((Throwable)exception), (Throwable)exception);
            }
            String string = exception.getMessage();
            if (string != null && string.length() < 8) {
                string = SQUtils.getStackTrace((Throwable)exception).substring(0, 100);
            }
            node.setError(10001, String.format("Exception in backtest: %s", string), exception);
            return node;
        }
    }

    private String getStrategyName(GPIDs gPIDs) {
        return String.format("Strategy %d.%d.%d", gPIDs.islandIndex + 1, gPIDs.generationIndex, gPIDs.nodeIndex);
    }

    private void setDismissalToFalse(BacktestSettings backtestSettings) {
        this.backtestSettings.dismissBadStrategies = 0;
        if (this.backtestSettings.crossChecks != null && this.backtestSettings.crossChecks.size() != 0) {
            ArrayList<ICrossCheck> arrayList = ProjectConfigHelper.cloneCrossChecks(this.backtestSettings.crossChecks);
        }
    }

    public BacktestEvaluator getClone() throws Exception {
        BacktestEvaluator backtestEvaluator = new BacktestEvaluator(this.backtestSettings.getClone(), this.lastEventListener, this.lastSettingsXml);
        return backtestEvaluator;
    }

    @Override
    public void destroy() {
        if (this.backtestRunner != null) {
            this.backtestRunner.stop();
        }
    }

    @Override
    public void stop() {
        if (this.backtestRunner != null) {
            this.backtestRunner.stop();
        }
    }
}

