/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.gp.FitnessCollectionData;

public class GPFitnessEvolutionData {
    public FitnessCollectionData[] generationData;
    public int islandIndex;
    public int generation = 0;
    public int populationSize = 0;

    public GPFitnessEvolutionData(int n, int n2) {
        this.islandIndex = n;
        this.generationData = new FitnessCollectionData[n2 + 2];
    }

    public void reset() {
        this.generation = 0;
    }
}

