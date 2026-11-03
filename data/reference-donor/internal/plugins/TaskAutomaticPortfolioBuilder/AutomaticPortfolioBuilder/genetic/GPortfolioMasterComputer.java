/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.L
 *  com.strategyquant.lib.SQTime
 *  com.strategyquant.tradinglib.CorrelationType
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.SampleTypes
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.conditions.DismissStruct
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  com.strategyquant.tradinglib.project.ProgressEngine
 *  com.strategyquant.tradinglib.project.ProjectStatusListener
 *  com.strategyquant.tradinglib.project.SQProject
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.lib.L;
import com.strategyquant.lib.SQTime;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMComputationListener;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioChecker;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioCombination;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioMasterComputer;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GPMasterComputer;
import com.strategyquant.tradinglib.CorrelationType;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.SampleTypes;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.conditions.DismissStruct;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import com.strategyquant.tradinglib.project.ProgressEngine;
import com.strategyquant.tradinglib.project.ProjectStatusListener;
import com.strategyquant.tradinglib.project.SQProject;
import java.math.BigInteger;
import java.util.ArrayList;

public class GPortfolioMasterComputer
extends PortfolioMasterComputer
implements PMComputationListener,
ProjectStatusListener {
    private int minStrategiesInPortfolio;
    private int maxStrategiesInPortfolio;
    private BigInteger numberOfPossiblePortfolios;
    private long startTime;
    private long genStartTime;
    private int period;
    private CorrelationType type;
    private double maxCorrelation;
    private boolean allowNegativeCorrelation;
    private boolean addEmptyPeriods;
    private PortfolioMasterFitness fitnessFunction;
    private int maxFromSector;
    private PortfolioChecker portfolioChecker;

    public GPortfolioMasterComputer(ArrayList<ResultsGroup> originalResults, SQProject project, ProgressEngine progressEngine, PortfolioMasterSettings settings) throws Exception {
        this.originalResults = originalResults;
        this.minStrategiesInPortfolio = settings.minStrategiesInPortfolio;
        this.maxStrategiesInPortfolio = settings.maxStrategiesInPortfolio;
        if (this.maxStrategiesInPortfolio >= originalResults.size()) {
            this.maxStrategiesInPortfolio = originalResults.size() - 1;
        }
        this.maxFromSector = settings.maxStrategiesSector;
        this.numberOfPossiblePortfolios = settings.numberOfPossiblePortfolios;
        this.fitnessFunction = settings.fitnessFunction;
        this.period = settings.correlationPeriod;
        this.type = settings.correlationType;
        this.maxCorrelation = settings.maxCorrelation;
        this.allowNegativeCorrelation = settings.allowNegativeCorrelation;
        this.addEmptyPeriods = settings.addEmptyPeriods;
        this.project = project;
        this.settings = settings;
        this.progressEngine = progressEngine;
        progressEngine.setProjectStatusListener((ProjectStatusListener)this);
    }

    @Override
    public void execute() throws Exception {
        this.startTime = System.currentTimeMillis();
        try {
            this.genStartTime = System.currentTimeMillis();
            this.beforeStart();
            this.portfolioChecker = new PortfolioChecker(this.period, this.type, this.maxCorrelation, this.allowNegativeCorrelation, this.addEmptyPeriods, this.maxFromSector, this.settings);
            this.portfolioChecker.setResults(this.originalResults);
            this.printLog("Genetic Portfolio Master");
            GPMasterComputer.run(this, this.fitnessFunction, this.originalResults.size(), this.minStrategiesInPortfolio, this.maxStrategiesInPortfolio, this.settings);
        }
        catch (Exception ex) {
            Log.error("GPortfolioMasterComputer error -  " + ex.getMessage(), (Throwable)ex);
            throw new Exception("GPortfolioMasterComputer error -  " + ex.getMessage(), ex);
        }
    }

    @Override
    public synchronized PortfolioCombination checkPortfolio(int[] combination) throws Exception {
        ++this.portfolioIndex;
        PortfolioCombination pc = new PortfolioCombination();
        pc.portfolioName = this.getPortfolioName(this.portfolioIndex);
        pc.portfolioIndexes = this.getPortfolioIndexes(combination);
        pc.dismiss = this.portfolioChecker.checkCorrectness(combination, pc.portfolioName);
        return pc;
    }

    @Override
    public synchronized void portfolioComputed(BacktestResult result) throws Exception {
        try {
            if (result.isDismissed()) {
                this.project.trackJob(null, result.getDismissalReason(), null, 0, 0L, 0L);
                this.printLog(result.getDismissalMessage());
                return;
            }
            ResultsGroup rg = result.getResult();
            DismissStruct dismiss = this.checkCustomConditions(rg);
            if (dismiss != null) {
                this.project.trackJob(null, dismiss.dismissReason, null, 0, 0L, 0L);
                this.printLog(L.t((String)"%s - dismissed, reason: %s", (Object[])new Object[]{rg.getName(), dismiss.dismissMessage}));
                return;
            }
            String fitness = this.fitnessFunction.getName() + " " + SampleTypes.typeToFullString((byte)this.settings.fitnessSampleType) + " " + rg.specialValues().getString(PortfolioMasterSettings.PMFitnessValue);
            this.printLog(L.t((String)"%s added. %s", (Object[])new Object[]{rg.getName(), fitness}));
            this.project.trackJob(null, 0, null, 0, 0L, 0L);
            this.settings.databankTarget.add(rg, true);
            this.settings.databankTarget.updateBestResults();
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            throw e;
        }
    }

    protected void done() {
        long stopTime = System.currentTimeMillis();
        float elapsedTime = (float)(stopTime - this.startTime) / 1000.0f;
        this.printLog(String.format(L.t((String)"Done in %s", (Object[])new Object[0]), SQTime.formatDateTime((long)Float.valueOf(elapsedTime).intValue())));
        System.gc();
    }

    @Override
    public boolean isStopped() {
        return this.progressEngine.isStopped();
    }

    @Override
    public synchronized void printLog(String text) {
        this.progressEngine.printToLogDebug(text);
    }

    @Override
    public void resetStats() {
    }

    @Override
    public void computePortfolio(int[] indexes) {
    }

    public void projectStatusChanged(int status) {
        if (status == 4) {
            GPMasterComputer.userAbort.abort();
        }
    }
}

