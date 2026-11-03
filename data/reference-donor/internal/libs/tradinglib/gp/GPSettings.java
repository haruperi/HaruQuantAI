/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.EvolutionPipeline;
import com.strategyquant.tradinglib.gp.IFitnessEvaluator;
import com.strategyquant.tradinglib.gp.IGPNode;
import com.strategyquant.tradinglib.gp.ISelectionStrategy;
import java.io.Serializable;

public class GPSettings<T extends IGPNode>
implements Serializable {
    private static final long serialVersionUID = 1L;
    public int populationSize;
    public int elitismSize;
    public int maxGenerations;
    public int numberOfIslands;
    public double migrationRate;
    public int migrationGenerationsModulo;
    public IRandomGenerator rng;
    public int decimationCoefficient;
    public boolean naturalFitness = true;
    public AbstractFactory<T> factory;
    public EvolutionPipeline<T> evolutionPipeline;
    public IFitnessEvaluator<? super T> evaluator;
    public ISelectionStrategy<? super T> selectionStrategy;
    public boolean printPopulationToLog = false;
    public boolean sendEveryCandidateEvent = true;
    public boolean sendLastPopulation = false;
    public boolean singleThreaded = false;
    public boolean restartOnFinish;
    public boolean restartOnStagnation;
    public int stagnationGenerationsToRestart;
    public int stagnationFitnessRestartType;
    public int evolutionUniquenessRetries = 0;
    public boolean freshBloodReplaceSimilar = false;
    public boolean freshBloodReplaceWeakest = false;
    public int replaceWeakestPct = 10;
    public int replaceWeakestGenerations = 5;
    public double trainingValidationRatio = 0.5;

    public GPSettings<T> clone(IRandomGenerator iRandomGenerator) {
        GPSettings<T> gPSettings = new GPSettings<T>();
        gPSettings.populationSize = this.populationSize;
        gPSettings.elitismSize = this.elitismSize;
        gPSettings.maxGenerations = this.maxGenerations;
        gPSettings.numberOfIslands = this.numberOfIslands;
        gPSettings.migrationRate = this.migrationRate;
        gPSettings.migrationGenerationsModulo = this.migrationGenerationsModulo;
        gPSettings.rng = iRandomGenerator;
        gPSettings.decimationCoefficient = this.decimationCoefficient;
        gPSettings.naturalFitness = this.naturalFitness;
        gPSettings.factory = this.factory.clone();
        gPSettings.evolutionPipeline = this.evolutionPipeline;
        gPSettings.evaluator = this.evaluator;
        gPSettings.selectionStrategy = this.selectionStrategy;
        gPSettings.printPopulationToLog = this.printPopulationToLog;
        gPSettings.sendEveryCandidateEvent = this.sendEveryCandidateEvent;
        gPSettings.sendLastPopulation = this.sendLastPopulation;
        gPSettings.singleThreaded = this.singleThreaded;
        gPSettings.restartOnFinish = this.restartOnFinish;
        gPSettings.restartOnStagnation = this.restartOnStagnation;
        gPSettings.stagnationGenerationsToRestart = this.stagnationGenerationsToRestart;
        gPSettings.stagnationFitnessRestartType = this.stagnationFitnessRestartType;
        gPSettings.trainingValidationRatio = this.trainingValidationRatio;
        gPSettings.evolutionUniquenessRetries = this.evolutionUniquenessRetries;
        gPSettings.freshBloodReplaceSimilar = this.freshBloodReplaceSimilar;
        gPSettings.freshBloodReplaceWeakest = this.freshBloodReplaceWeakest;
        gPSettings.replaceWeakestPct = this.replaceWeakestPct;
        gPSettings.replaceWeakestGenerations = this.replaceWeakestGenerations;
        return gPSettings;
    }
}

