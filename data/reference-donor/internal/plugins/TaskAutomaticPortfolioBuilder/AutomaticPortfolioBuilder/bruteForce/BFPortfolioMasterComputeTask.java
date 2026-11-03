/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMComputationListener;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMPortfolioComputer;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioCombination;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import java.util.concurrent.Callable;

public class BFPortfolioMasterComputeTask
implements Callable<BacktestResult> {
    private PMComputationListener listener;
    private PortfolioMasterSettings settings;
    private int[] indexes;

    public BFPortfolioMasterComputeTask(int[] indexes, PMComputationListener listener, PortfolioMasterSettings settings) {
        this.indexes = indexes;
        this.listener = listener;
        this.settings = settings;
    }

    @Override
    public BacktestResult call() throws Exception {
        PMPortfolioComputer portfolioComputer = new PMPortfolioComputer();
        PortfolioCombination pc = this.listener.checkPortfolio(this.indexes);
        if (pc.dismiss != null) {
            return new BacktestResult(pc.dismiss);
        }
        ResultsGroup result = portfolioComputer.createPortfolio(this.listener.getResults(this.indexes), pc.portfolioName, this.settings);
        PortfolioMasterFitness ff = this.settings.fitnessFunction;
        double value = ff.compute(result, this.settings.fitnessSampleType);
        result.specialValues().set(PortfolioMasterSettings.PMFitnessValue, (Object)ff.print(value));
        result.portfolio().setFitness((byte)10, ff.transformToFitnessRange(ff.compute(result, (byte)10)));
        result.portfolio().setFitness((byte)20, ff.transformToFitnessRange(ff.compute(result, (byte)20)));
        result.portfolio().setFitness((byte)127, ff.transformToFitnessRange(ff.compute(result, (byte)127)));
        result.setNote(pc.portfolioIndexes);
        return new BacktestResult(result);
    }
}

