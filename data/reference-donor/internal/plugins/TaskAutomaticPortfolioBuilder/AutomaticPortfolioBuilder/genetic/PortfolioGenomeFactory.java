/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.uncommons.watchmaker.framework.factories.AbstractCandidateFactory
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.GenomeSettings;
import com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic.PortfolioGenome;
import java.util.Random;
import org.uncommons.watchmaker.framework.factories.AbstractCandidateFactory;

public class PortfolioGenomeFactory
extends AbstractCandidateFactory<PortfolioGenome> {
    private GenomeSettings settings;

    public PortfolioGenomeFactory(GenomeSettings settings) {
        this.settings = settings;
    }

    public PortfolioGenome generateRandomCandidate(Random rng) {
        int portfolioSize = this.settings.minStrategiesInPortfolio;
        if (this.settings.maxStrategiesInPortfolio > this.settings.minStrategiesInPortfolio) {
            portfolioSize += rng.nextInt(this.settings.maxStrategiesInPortfolio - this.settings.minStrategiesInPortfolio + 1);
        }
        PortfolioGenome.StrategyGene[] genes = new PortfolioGenome.StrategyGene[portfolioSize];
        for (int i = 0; i < 1000; ++i) {
            this.generatePortfolio(genes);
            if (!PortfolioGenome.checkPortfolioIsCorrect(genes)) continue;
            PortfolioGenome portfolio = new PortfolioGenome(genes);
            return portfolio;
        }
        throw new IllegalArgumentException("Cannot generate any portfolio under these settings!");
    }

    private void generatePortfolio(PortfolioGenome.StrategyGene[] genes) {
        for (int i = 0; i < genes.length; ++i) {
            int index = this.settings.rng.nextInt(this.settings.numberOfStrategies - i);
            genes[i] = new PortfolioGenome.StrategyGene(PortfolioGenome.findXthAvailableGeneNumber(index, genes, i, this.settings.numberOfStrategies));
        }
    }
}

