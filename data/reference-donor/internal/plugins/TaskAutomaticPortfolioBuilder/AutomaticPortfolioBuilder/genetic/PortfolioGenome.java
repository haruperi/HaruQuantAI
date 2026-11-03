/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import java.util.Arrays;
import java.util.Comparator;

public class PortfolioGenome {
    private final StrategyGene[] strategyGenes;
    private final StrategyGenesComparator comparator = new StrategyGenesComparator();
    private final int hash;
    private int generation;
    private double fitness;

    public PortfolioGenome(StrategyGene[] strategyGenes) {
        Arrays.sort(strategyGenes, this.comparator);
        this.strategyGenes = strategyGenes;
        this.hash = this.computeHash();
    }

    private int computeHash() {
        int[] arr = new int[this.strategyGenes.length];
        for (int i = 0; i < this.strategyGenes.length; ++i) {
            arr[i] = this.strategyGenes[i].getNumber();
        }
        return Arrays.hashCode(arr);
    }

    public StrategyGene[] getGenes() {
        return this.strategyGenes;
    }

    public String toString() {
        if (this.strategyGenes == null) {
            return "NULLL";
        }
        String str = "[";
        for (int i = 0; i < this.strategyGenes.length; ++i) {
            str = str + this.strategyGenes[i].getNumber() + ",";
        }
        str = str.substring(0, str.length() - 1);
        str = str + "]";
        return str;
    }

    public StrategyGene[] cloneGenes() {
        return PortfolioGenome.cloneGenes(this.strategyGenes);
    }

    public static StrategyGene[] cloneGenes(StrategyGene[] genes) {
        StrategyGene[] newGenes = new StrategyGene[genes.length];
        for (int i = 0; i < genes.length; ++i) {
            newGenes[i] = genes[i].clone();
        }
        return newGenes;
    }

    public static boolean checkPortfolioIsCorrect(StrategyGene[] genes) {
        for (int i = 0; i < genes.length; ++i) {
            for (int j = i + 1; j < genes.length; ++j) {
                if (i == j || genes[i].getNumber() != genes[j].getNumber()) continue;
                return false;
            }
        }
        return true;
    }

    public int getHash() {
        return this.hash;
    }

    public void setGeneration(int generation) {
        this.generation = generation;
    }

    public void setFitness(double fitness) {
        this.fitness = fitness;
    }

    public int getGeneration() {
        return this.generation;
    }

    public double getFitness() {
        return this.fitness;
    }

    public static int findXthAvailableGeneNumber(int index, StrategyGene[] genes, int genesSoFar, int totalAvailableNumbers) {
        int count = 0;
        for (int i = 0; i < totalAvailableNumbers; ++i) {
            if (PortfolioGenome.containsNumber(genes, genesSoFar, i)) continue;
            if (index == count) {
                return i;
            }
            ++count;
        }
        return -1;
    }

    private static boolean containsNumber(StrategyGene[] genes, int genesSoFar, int number) {
        for (int i = 0; i < genesSoFar; ++i) {
            if (genes[i].getNumber() != number) continue;
            return true;
        }
        return false;
    }

    public int[] getIndexes() {
        StrategyGene[] genes = this.getGenes();
        int[] indexes = new int[genes.length];
        for (int i = 0; i < genes.length; ++i) {
            indexes[i] = genes[i].getNumber();
        }
        return indexes;
    }

    class StrategyGenesComparator
    implements Comparator<StrategyGene> {
        StrategyGenesComparator() {
        }

        @Override
        public int compare(StrategyGene o1, StrategyGene o2) {
            return o1.number - o2.number;
        }
    }

    public static final class StrategyGene {
        private final int number;
        private final String name;

        public StrategyGene(int number, String name) {
            this.number = number;
            this.name = name;
        }

        public StrategyGene(int number) {
            if (number < 0) {
                throw new IllegalArgumentException("Cannot use -1 as argument for StrategyGene");
            }
            this.number = number;
            this.name = "Strategy " + number;
        }

        public int getNumber() {
            return this.number;
        }

        public String getName() {
            return this.name;
        }

        public StrategyGene clone() {
            return new StrategyGene(this.number, this.name);
        }
    }
}

