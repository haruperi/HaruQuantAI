/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.ResultsGroup
 *  com.strategyquant.tradinglib.backtestrunner.BacktestResult
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 *  org.uncommons.watchmaker.framework.FitnessEvaluator
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMComputationListener;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMPortfolioComputer;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PortfolioCombination;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GenomeSettings;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioFitnessCache;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import com.strategyquant.tradinglib.ResultsGroup;
import com.strategyquant.tradinglib.backtestrunner.BacktestResult;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.uncommons.watchmaker.framework.FitnessEvaluator;

public class PortfolioGenomeEvaluator
implements FitnessEvaluator<PortfolioGenome> {
    public static final Logger Log = LoggerFactory.getLogger((String)"PortfolioGenomeEvaluator");
    private GenomeSettings settings;
    private PMComputationListener listener = null;
    private PMPortfolioComputer portfolioComputer = new PMPortfolioComputer();
    private static PortfolioFitnessCache fitnessCache = new PortfolioFitnessCache();
    private PortfolioMasterSettings pmSettings;

    public PortfolioGenomeEvaluator(GenomeSettings settings, PMComputationListener listener, PortfolioMasterSettings pmSettings) {
        this.settings = settings;
        this.listener = listener;
        this.pmSettings = pmSettings;
        fitnessCache.reset();
    }

    public double getFitness(PortfolioGenome candidate, List<? extends PortfolioGenome> population) {
        try {
            int hashKey = candidate.getHash();
            double fitness = fitnessCache.getFitness(hashKey);
            if (fitness >= 0.0) {
                return fitness;
            }
            int[] indexes = candidate.getIndexes();
            PortfolioCombination pc = this.listener.checkPortfolio(indexes);
            if (pc.dismiss != null) {
                fitnessCache.setFitness(hashKey, 0.0);
                this.listener.portfolioComputed(new BacktestResult(pc.dismiss));
                return 0.0;
            }
            ResultsGroup result = this.portfolioComputer.createPortfolio(this.listener.getResults(indexes), pc.portfolioName, this.pmSettings);
            PortfolioMasterFitness ff = this.pmSettings.fitnessFunction;
            double value = ff.compute(result, this.pmSettings.fitnessSampleType);
            result.specialValues().set(PortfolioMasterSettings.PMFitnessValue, (Object)ff.print(value));
            result.portfolio().setFitness((byte)10, ff.transformToFitnessRange(ff.compute(result, (byte)10)));
            result.portfolio().setFitness((byte)20, ff.transformToFitnessRange(ff.compute(result, (byte)20)));
            result.portfolio().setFitness((byte)127, ff.transformToFitnessRange(ff.compute(result, (byte)127)));
            result.setNote(pc.portfolioIndexes);
            fitness = result.getFitness();
            fitnessCache.setFitness(hashKey, fitness);
            this.listener.portfolioComputed(new BacktestResult(result));
            return fitness;
        }
        catch (Exception e) {
            Log.error("Exc.", (Throwable)e);
            return 0.0;
        }
    }

    public boolean isNatural() {
        return this.settings.fitnessMaximize;
    }
}

