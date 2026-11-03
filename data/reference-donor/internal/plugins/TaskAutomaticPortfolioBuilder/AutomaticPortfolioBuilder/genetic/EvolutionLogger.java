/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.EvolutionObserver
 *  org.uncommons.watchmaker.framework.PopulationData
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.bruteForce.PMComputationListener;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import org.uncommons.watchmaker.framework.EvolutionObserver;
import org.uncommons.watchmaker.framework.PopulationData;

public class EvolutionLogger
implements EvolutionObserver<PortfolioGenome> {
    private PMComputationListener listener;

    public EvolutionLogger(PMComputationListener listener) {
        this.listener = listener;
    }

    public void populationUpdate(PopulationData<? extends PortfolioGenome> data) {
        this.listener.printLog("-------- Generation " + data.getGenerationNumber());
        ((PortfolioGenome)data.getBestCandidate()).setGeneration(data.getGenerationNumber());
        ((PortfolioGenome)data.getBestCandidate()).setFitness(data.getBestCandidateFitness());
    }
}

