/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.plugin.Task.impl.AutomaticPortfolioBuilder.genetic;

import java.util.HashMap;

public class PortfolioFitnessCache {
    private static final int MAX_CACHE_SIZE = 100000;
    private HashMap<Integer, Double> cache = new HashMap();

    public void reset() {
        this.cache.clear();
    }

    public synchronized double getFitness(int portfolioHashKey) {
        if (this.cache.containsKey(portfolioHashKey)) {
            return this.cache.get(portfolioHashKey);
        }
        return -1.0;
    }

    public synchronized void setFitness(int portfolioHashKey, double fitness) {
        if (!this.cache.containsKey(portfolioHashKey)) {
            if (this.cache.size() > 100000) {
                this.cache.clear();
            }
            this.cache.put(portfolioHashKey, fitness);
        }
    }
}

