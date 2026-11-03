/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.EvolutionaryOperator
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GenomeSettings;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;
import org.uncommons.watchmaker.framework.EvolutionaryOperator;

public class PortfolioGenomeMutation
implements EvolutionaryOperator<PortfolioGenome> {
    private GenomeSettings settings;

    public PortfolioGenomeMutation(GenomeSettings settings) {
        this.settings = settings;
    }

    public List<PortfolioGenome> apply(List<PortfolioGenome> selectedCandidates, Random rng) {
        ArrayList<PortfolioGenome> mutatedCandidates = new ArrayList<PortfolioGenome>(selectedCandidates.size());
        for (PortfolioGenome sudoku : selectedCandidates) {
            mutatedCandidates.add(this.mutate(sudoku, rng));
        }
        return mutatedCandidates;
    }

    private PortfolioGenome mutate(PortfolioGenome portfolio, Random rng) {
        PortfolioGenome.StrategyGene[] genes = portfolio.cloneGenes();
        boolean geneMutated = false;
        for (int i = 0; i < this.settings.mutationPoints; ++i) {
            if (!this.settings.mutationProbability.nextEvent(rng)) continue;
            int index = rng.nextInt(genes.length);
            genes[index] = this.mutateGene(index, genes);
            geneMutated = true;
        }
        if (this.settings.maxStrategiesInPortfolio != this.settings.minStrategiesInPortfolio && this.settings.mutationResizeProbability.nextEvent(rng)) {
            if (genes.length < this.settings.maxStrategiesInPortfolio) {
                genes = this.addGene(genes, rng);
            } else if (genes.length > this.settings.minStrategiesInPortfolio) {
                genes = this.removeGene(genes, rng.nextInt(genes.length));
            }
        }
        PortfolioGenome newPortfolio = new PortfolioGenome(genes);
        if (geneMutated) {
            // empty if block
        }
        return newPortfolio;
    }

    private PortfolioGenome.StrategyGene[] addGene(PortfolioGenome.StrategyGene[] genes, Random rng) {
        PortfolioGenome.StrategyGene[] newGenes = new PortfolioGenome.StrategyGene[genes.length + 1];
        for (int i = 0; i < genes.length; ++i) {
            newGenes[i] = genes[i];
        }
        int newIndex = this.settings.rng.nextInt(this.settings.numberOfStrategies - genes.length);
        newGenes[genes.length] = new PortfolioGenome.StrategyGene(PortfolioGenome.findXthAvailableGeneNumber(newIndex, genes, genes.length, this.settings.numberOfStrategies));
        return newGenes;
    }

    private PortfolioGenome.StrategyGene[] removeGene(PortfolioGenome.StrategyGene[] genes, int indexToRemove) {
        PortfolioGenome.StrategyGene[] newGenes = new PortfolioGenome.StrategyGene[genes.length - 1];
        int j = 0;
        for (int i = 0; i < genes.length; ++i) {
            if (i == indexToRemove) continue;
            newGenes[j++] = genes[i];
        }
        return newGenes;
    }

    private PortfolioGenome.StrategyGene mutateGene(int index, PortfolioGenome.StrategyGene[] genes) {
        int newIndex = this.settings.rng.nextInt(this.settings.numberOfStrategies - genes.length);
        return new PortfolioGenome.StrategyGene(PortfolioGenome.findXthAvailableGeneNumber(newIndex, genes, genes.length, this.settings.numberOfStrategies));
    }
}

