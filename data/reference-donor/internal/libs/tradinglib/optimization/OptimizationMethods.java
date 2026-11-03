/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.tradinglib.optimization.PopulationGenerations;

public class OptimizationMethods {
    public static final int Automatic = 0;
    public static final int BruteForce = 1;
    public static final int GeneticOptimization = 2;

    public static PopulationGenerations suggestPopulationGenerations(long l, int n, int n2) {
        PopulationGenerations populationGenerations = new PopulationGenerations();
        populationGenerations.method = n;
        if (n2 == 1000000001) {
            populationGenerations.method = 1;
            return populationGenerations;
        }
        if (n2 < 0) {
            n2 = 10000;
        }
        if ((double)l <= (double)n2 * 1.3 && (populationGenerations.method == 1 || populationGenerations.method == 0)) {
            populationGenerations.method = 1;
            return populationGenerations;
        }
        populationGenerations.generations = 10;
        populationGenerations.method = 2;
        long l2 = Math.min(l, (long)n2);
        populationGenerations.population = (int)(1L * (l2 / (long)populationGenerations.generations));
        if (populationGenerations.population > 500) {
            populationGenerations.generations = (int)((double)populationGenerations.generations * Math.ceil(populationGenerations.population / 500));
            populationGenerations.population = 500;
        }
        if (populationGenerations.population < 1000) {
            populationGenerations.population -= populationGenerations.population % 10;
        }
        if (populationGenerations.population == 0) {
            populationGenerations.population = 10;
        }
        if (populationGenerations.generations == 0) {
            populationGenerations.generations = 3;
        }
        return populationGenerations;
    }

    public static long getTotalCombinations(long l, PopulationGenerations populationGenerations, int n) {
        if (n > 0) {
            return n;
        }
        if (populationGenerations.method == 1) {
            return l;
        }
        return (long)populationGenerations.population * (long)populationGenerations.generations;
    }
}

