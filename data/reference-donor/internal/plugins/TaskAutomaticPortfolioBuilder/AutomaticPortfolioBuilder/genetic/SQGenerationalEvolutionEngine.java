/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.CandidateFactory
 *  org.uncommons.watchmaker.framework.EvaluatedCandidate
 *  org.uncommons.watchmaker.framework.EvolutionEngine
 *  org.uncommons.watchmaker.framework.EvolutionObserver
 *  org.uncommons.watchmaker.framework.EvolutionUtils
 *  org.uncommons.watchmaker.framework.EvolutionaryOperator
 *  org.uncommons.watchmaker.framework.FitnessEvaluator
 *  org.uncommons.watchmaker.framework.PopulationData
 *  org.uncommons.watchmaker.framework.SelectionStrategy
 *  org.uncommons.watchmaker.framework.TerminationCondition
 *  org.uncommons.watchmaker.framework.termination.UserAbort
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.FitnessEvaluationWorker;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.FitnessEvalutationTask;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.List;
import java.util.Random;
import java.util.Set;
import java.util.concurrent.CopyOnWriteArraySet;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import org.uncommons.watchmaker.framework.CandidateFactory;
import org.uncommons.watchmaker.framework.EvaluatedCandidate;
import org.uncommons.watchmaker.framework.EvolutionEngine;
import org.uncommons.watchmaker.framework.EvolutionObserver;
import org.uncommons.watchmaker.framework.EvolutionUtils;
import org.uncommons.watchmaker.framework.EvolutionaryOperator;
import org.uncommons.watchmaker.framework.FitnessEvaluator;
import org.uncommons.watchmaker.framework.PopulationData;
import org.uncommons.watchmaker.framework.SelectionStrategy;
import org.uncommons.watchmaker.framework.TerminationCondition;
import org.uncommons.watchmaker.framework.termination.UserAbort;

public class SQGenerationalEvolutionEngine<T>
implements EvolutionEngine<T> {
    private static FitnessEvaluationWorker concurrentWorker = null;
    private final Set<EvolutionObserver<? super T>> observers = new CopyOnWriteArraySet<EvolutionObserver<? super T>>();
    private final Random rng;
    private final CandidateFactory<T> candidateFactory;
    private volatile boolean singleThreaded = false;
    private List<TerminationCondition> satisfiedTerminationConditions;
    private final EvolutionaryOperator<T> evolutionScheme;
    private final FitnessEvaluator<? super T> fitnessEvaluator;
    private final SelectionStrategy<? super T> selectionStrategy;
    private UserAbort userAbort;

    public SQGenerationalEvolutionEngine(CandidateFactory<T> candidateFactory, EvolutionaryOperator<T> evolutionScheme, FitnessEvaluator<? super T> fitnessEvaluator, SelectionStrategy<? super T> selectionStrategy, Random rng, UserAbort userAbort) {
        this.candidateFactory = candidateFactory;
        this.fitnessEvaluator = fitnessEvaluator;
        this.rng = rng;
        this.evolutionScheme = evolutionScheme;
        this.selectionStrategy = selectionStrategy;
        this.userAbort = userAbort;
    }

    protected List<EvaluatedCandidate<T>> nextEvolutionStep(List<EvaluatedCandidate<T>> evaluatedPopulation, int eliteCount, Random rng) {
        List<Object> population = new ArrayList(evaluatedPopulation.size());
        ArrayList<Object> elite = new ArrayList<Object>(eliteCount);
        Iterator<EvaluatedCandidate<T>> iterator = evaluatedPopulation.iterator();
        while (elite.size() < eliteCount) {
            elite.add(iterator.next().getCandidate());
        }
        population.addAll(this.selectionStrategy.select(evaluatedPopulation, this.fitnessEvaluator.isNatural(), evaluatedPopulation.size() - eliteCount, rng));
        population = this.evolutionScheme.apply(population, rng);
        population.addAll(elite);
        return this.evaluatePopulation(population);
    }

    public T evolve(int populationSize, int eliteCount, TerminationCondition ... conditions) {
        return this.evolve(populationSize, eliteCount, Collections.emptySet(), conditions);
    }

    public T evolve(int populationSize, int eliteCount, Collection<T> seedCandidates, TerminationCondition ... conditions) {
        List<EvaluatedCandidate<T>> list = this.evolvePopulation(populationSize, eliteCount, seedCandidates, conditions);
        if (list == null) {
            return null;
        }
        return (T)list.get(0).getCandidate();
    }

    public List<EvaluatedCandidate<T>> evolvePopulation(int populationSize, int eliteCount, TerminationCondition ... conditions) {
        return this.evolvePopulation(populationSize, eliteCount, Collections.emptySet(), conditions);
    }

    public List<EvaluatedCandidate<T>> evolvePopulation(int populationSize, int eliteCount, Collection<T> seedCandidates, TerminationCondition ... conditions) {
        if (eliteCount < 0 || eliteCount >= populationSize) {
            throw new IllegalArgumentException("Elite count must be non-negative and less than population size.");
        }
        if (conditions.length == 0) {
            throw new IllegalArgumentException("At least one TerminationCondition must be specified.");
        }
        this.satisfiedTerminationConditions = null;
        int currentGenerationIndex = 0;
        long startTime = System.currentTimeMillis();
        List population = this.candidateFactory.generateInitialPopulation(populationSize, seedCandidates, this.rng);
        List<EvaluatedCandidate<T>> evaluatedPopulation = this.evaluatePopulation(population);
        if (evaluatedPopulation == null) {
            return null;
        }
        EvolutionUtils.sortEvaluatedPopulation(evaluatedPopulation, (boolean)this.fitnessEvaluator.isNatural());
        PopulationData data = EvolutionUtils.getPopulationData(evaluatedPopulation, (boolean)this.fitnessEvaluator.isNatural(), (int)eliteCount, (int)currentGenerationIndex, (long)startTime);
        this.notifyPopulationChange(data);
        List satisfiedConditions = EvolutionUtils.shouldContinue((PopulationData)data, (TerminationCondition[])conditions);
        while (satisfiedConditions == null) {
            ++currentGenerationIndex;
            if ((evaluatedPopulation = this.nextEvolutionStep(evaluatedPopulation, eliteCount, this.rng)) == null) {
                return null;
            }
            EvolutionUtils.sortEvaluatedPopulation(evaluatedPopulation, (boolean)this.fitnessEvaluator.isNatural());
            data = EvolutionUtils.getPopulationData(evaluatedPopulation, (boolean)this.fitnessEvaluator.isNatural(), (int)eliteCount, (int)currentGenerationIndex, (long)startTime);
            this.notifyPopulationChange(data);
            satisfiedConditions = EvolutionUtils.shouldContinue((PopulationData)data, (TerminationCondition[])conditions);
        }
        this.satisfiedTerminationConditions = satisfiedConditions;
        return evaluatedPopulation;
    }

    protected List<EvaluatedCandidate<T>> evaluatePopulation(List<T> population) {
        ArrayList<EvaluatedCandidate<T>> evaluatedPopulation = new ArrayList<EvaluatedCandidate<T>>(population.size());
        if (this.singleThreaded) {
            for (T candidate : population) {
                if (this.userAbort != null && this.userAbort.isAborted()) {
                    return null;
                }
                evaluatedPopulation.add(new EvaluatedCandidate(candidate, this.fitnessEvaluator.getFitness(candidate, population)));
            }
        } else {
            try {
                List<T> unmodifiablePopulation = Collections.unmodifiableList(population);
                ArrayList<Future<EvaluatedCandidate<T>>> results = new ArrayList<Future<EvaluatedCandidate<T>>>(population.size());
                for (T t : population) {
                    if (this.userAbort != null && this.userAbort.isAborted()) {
                        this.cancelResults(results);
                        return null;
                    }
                    results.add(SQGenerationalEvolutionEngine.getSharedWorker().submit(new FitnessEvalutationTask<T>(this.fitnessEvaluator, t, unmodifiablePopulation)));
                }
                for (Future future : results) {
                    if (this.userAbort != null && this.userAbort.isAborted()) {
                        this.cancelResults(results);
                        return null;
                    }
                    evaluatedPopulation.add((EvaluatedCandidate)future.get());
                }
            }
            catch (ExecutionException ex) {
                throw new IllegalStateException("Fitness evaluation task execution failed.", ex);
            }
            catch (InterruptedException ex) {
                Thread.currentThread().interrupt();
            }
        }
        return evaluatedPopulation;
    }

    private void cancelResults(List<Future<EvaluatedCandidate<T>>> results) {
        for (Future<EvaluatedCandidate<T>> result : results) {
            result.cancel(true);
        }
    }

    public List<TerminationCondition> getSatisfiedTerminationConditions() {
        if (this.satisfiedTerminationConditions == null) {
            throw new IllegalStateException("EvolutionEngine has not terminated.");
        }
        return Collections.unmodifiableList(this.satisfiedTerminationConditions);
    }

    public void addEvolutionObserver(EvolutionObserver<? super T> observer) {
        this.observers.add(observer);
    }

    public void removeEvolutionObserver(EvolutionObserver<? super T> observer) {
        this.observers.remove(observer);
    }

    private void notifyPopulationChange(PopulationData<T> data) {
        for (EvolutionObserver<? super T> evolutionObserver : this.observers) {
            evolutionObserver.populationUpdate(data);
        }
    }

    public void setSingleThreaded(boolean singleThreaded) {
        this.singleThreaded = singleThreaded;
    }

    private static synchronized FitnessEvaluationWorker getSharedWorker() {
        if (concurrentWorker == null) {
            concurrentWorker = new FitnessEvaluationWorker();
        }
        return concurrentWorker;
    }
}

