/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.operators.AbstractCrossover
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GenomeSettings;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.uncommons.watchmaker.framework.operators.AbstractCrossover;

public class PortfolioGenomeCrossover
extends AbstractCrossover<PortfolioGenome> {
    private GenomeSettings settings;

    public PortfolioGenomeCrossover(GenomeSettings settings) {
        super(settings.crossoverPoints, settings.crossoverProbability);
        this.settings = settings;
    }

    protected List<PortfolioGenome> mate(PortfolioGenome parent1, PortfolioGenome parent2, int numberOfCrossoverPoints, Random rng) {
        List<PortfolioGenome> result;
        for (int i = 0; i < 1000; ++i) {
            result = this.mateOnce(parent1, parent2, numberOfCrossoverPoints, rng);
            if (result == null) continue;
            return result;
        }
        result = new ArrayList<PortfolioGenome>(2);
        result.add(parent1);
        result.add(parent2);
        return result;
    }

    private List<PortfolioGenome> mateOnce(PortfolioGenome parent1, PortfolioGenome parent2, int numberOfCrossoverPoints, Random rng) {
        PortfolioGenome.StrategyGene[] offspring1 = this.copyParent(parent1);
        PortfolioGenome.StrategyGene[] offspring2 = this.copyParent(parent2);
        for (int i = 0; i < numberOfCrossoverPoints; ++i) {
            int copyIndexFrom = rng.nextInt(offspring1.length);
            int copyLength = 1 + rng.nextInt(offspring1.length);
            PortfolioGenome.StrategyGene[] temp = this.copyParent(parent1);
            this.copyGenes(offspring1, temp, copyIndexFrom, copyLength);
            this.copyGenes(offspring2, offspring1, copyIndexFrom, copyLength);
            this.copyGenes(temp, offspring2, copyIndexFrom, copyLength);
        }
        offspring1 = this.fixGenome(offspring1);
        offspring2 = this.fixGenome(offspring2);
        if (!PortfolioGenome.checkPortfolioIsCorrect(offspring1)) {
            return null;
        }
        if (!PortfolioGenome.checkPortfolioIsCorrect(offspring2)) {
            return null;
        }
        PortfolioGenome child1 = new PortfolioGenome(offspring1);
        PortfolioGenome child2 = new PortfolioGenome(offspring2);
        ArrayList<PortfolioGenome> result = new ArrayList<PortfolioGenome>(2);
        result.add(child1);
        result.add(child2);
        return result;
    }

    private PortfolioGenome.StrategyGene[] fixGenome(PortfolioGenome.StrategyGene[] genes) {
        int countCorrectGenes = 0;
        for (int i = 0; i < genes.length; ++i) {
            if (genes[i] == null) continue;
            ++countCorrectGenes;
        }
        PortfolioGenome.StrategyGene[] newGenes = new PortfolioGenome.StrategyGene[countCorrectGenes];
        int j = 0;
        for (int i = 0; i < genes.length; ++i) {
            if (genes[i] == null) continue;
            newGenes[j++] = genes[i];
        }
        return newGenes;
    }

    private void copyGenes(PortfolioGenome.StrategyGene[] source, PortfolioGenome.StrategyGene[] destination, int copyIndexFrom, int copyLength) {
        for (int i = copyIndexFrom; i < copyIndexFrom + copyLength; ++i) {
            if (i >= destination.length || source[i] == null) continue;
            destination[i] = source[i].clone();
        }
    }

    private PortfolioGenome.StrategyGene[] copyParent(PortfolioGenome parent) {
        PortfolioGenome.StrategyGene[] genes = new PortfolioGenome.StrategyGene[this.settings.maxStrategiesInPortfolio];
        PortfolioGenome.StrategyGene[] parentGenes = parent.getGenes();
        for (int i = 0; i < parentGenes.length; ++i) {
            genes[i] = parentGenes[i].clone();
        }
        return genes;
    }
}

