/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness
 *  com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings
 *  org.uncommons.maths.random.MersenneTwisterRNG
 *  org.uncommons.maths.random.Probability
 *  org.uncommons.watchmaker.framework.CandidateFactory
 *  org.uncommons.watchmaker.framework.EvolutionaryOperator
 *  org.uncommons.watchmaker.framework.SelectionStrategy
 *  org.uncommons.watchmaker.framework.TerminationCondition
 *  org.uncommons.watchmaker.framework.operators.EvolutionPipeline
 *  org.uncommons.watchmaker.framework.selection.RouletteWheelSelection
 *  org.uncommons.watchmaker.framework.termination.GenerationCount
 *  org.uncommons.watchmaker.framework.termination.Stagnation
 *  org.uncommons.watchmaker.framework.termination.UserAbort
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMComputationListener;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.EvolutionLogger;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GenomeSettings;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenomeEvaluator;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenomeFactory;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenomeMutation;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.SQGenerationalEvolutionEngine;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness;
import com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterSettings;
import java.util.ArrayList;
import org.uncommons.maths.random.MersenneTwisterRNG;
import org.uncommons.maths.random.Probability;
import org.uncommons.watchmaker.framework.CandidateFactory;
import org.uncommons.watchmaker.framework.EvolutionaryOperator;
import org.uncommons.watchmaker.framework.SelectionStrategy;
import org.uncommons.watchmaker.framework.TerminationCondition;
import org.uncommons.watchmaker.framework.operators.EvolutionPipeline;
import org.uncommons.watchmaker.framework.selection.RouletteWheelSelection;
import org.uncommons.watchmaker.framework.termination.GenerationCount;
import org.uncommons.watchmaker.framework.termination.Stagnation;
import org.uncommons.watchmaker.framework.termination.UserAbort;

public class GPMasterComputer {
    public static UserAbort userAbort = new UserAbort();

    public static void run(PMComputationListener listener, PortfolioMasterFitness fitnessFunction, int numberOfStrategies, int minStrategiesInPortfolio, int maxStrategiesInPortfolio, PortfolioMasterSettings pmSettings) {
        int populationSize = pmSettings.populationSize;
        int generations = pmSettings.generations;
        boolean runContinually = pmSettings.runContinually;
        boolean restartAfterStagnation = pmSettings.restartAfterStagnation;
        int generationLimit = pmSettings.generationLimit;
        while (true) {
            GenomeSettings settings = new GenomeSettings();
            settings.IsPct = pmSettings.IsPct;
            settings.reverseSample = pmSettings.reverseSample;
            settings.numberOfStrategies = numberOfStrategies;
            settings.minStrategiesInPortfolio = minStrategiesInPortfolio;
            settings.maxStrategiesInPortfolio = maxStrategiesInPortfolio;
            settings.populationSize = populationSize;
            settings.elitism = 1;
            settings.fitnessMaximize = pmSettings.fitnessFunction.getValueType() == 1;
            settings.singleThreaded = false;
            settings.userAbort = userAbort;
            settings.crossoverPoints = 1;
            settings.crossoverProbability = new Probability(0.8);
            settings.mutationPoints = 1;
            settings.mutationProbability = new Probability(0.5);
            settings.mutationResizeProbability = new Probability(0.1);
            settings.rng = new MersenneTwisterRNG();
            settings.userAbort.reset();
            ArrayList<PortfolioGenomeMutation> operators = new ArrayList<PortfolioGenomeMutation>(2);
            operators.add(new PortfolioGenomeMutation(settings));
            EvolutionPipeline pipeline = new EvolutionPipeline(operators);
            SQGenerationalEvolutionEngine<PortfolioGenome> engine = new SQGenerationalEvolutionEngine<PortfolioGenome>((CandidateFactory<PortfolioGenome>)new PortfolioGenomeFactory(settings), (EvolutionaryOperator<PortfolioGenome>)pipeline, new PortfolioGenomeEvaluator(settings, listener, pmSettings), (SelectionStrategy<PortfolioGenome>)new RouletteWheelSelection(), settings.rng, settings.userAbort);
            engine.addEvolutionObserver(new EvolutionLogger(listener));
            if (settings.singleThreaded) {
                engine.setSingleThreaded(true);
            }
            PortfolioGenome bestCandidate = restartAfterStagnation ? engine.evolve(settings.populationSize, settings.elitism, new TerminationCondition[]{new GenerationCount(generations), new Stagnation(generationLimit, true, true), settings.userAbort}) : engine.evolve(settings.populationSize, settings.elitism, new TerminationCondition[]{new GenerationCount(generations), settings.userAbort});
            if (!runContinually || listener.isStopped()) break;
            listener.printLog("New genetic run =================================================");
            listener.resetStats();
        }
    }
}

