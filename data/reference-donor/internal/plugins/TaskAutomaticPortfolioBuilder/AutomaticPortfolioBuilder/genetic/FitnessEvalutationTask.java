/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.EvaluatedCandidate
 *  org.uncommons.watchmaker.framework.FitnessEvaluator
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import java.util.List;
import java.util.concurrent.Callable;
import org.uncommons.watchmaker.framework.EvaluatedCandidate;
import org.uncommons.watchmaker.framework.FitnessEvaluator;

class FitnessEvalutationTask<T>
implements Callable<EvaluatedCandidate<T>> {
    private final FitnessEvaluator<? super T> fitnessEvaluator;
    private final T candidate;
    private final List<T> population;

    FitnessEvalutationTask(FitnessEvaluator<? super T> fitnessEvaluator, T candidate, List<T> population) {
        this.fitnessEvaluator = fitnessEvaluator;
        this.candidate = candidate;
        this.population = population;
    }

    @Override
    public EvaluatedCandidate<T> call() {
        return new EvaluatedCandidate(this.candidate, this.fitnessEvaluator.getFitness(this.candidate, this.population));
    }
}

