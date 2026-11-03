/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib;

import com.strategyquant.tradinglib.gp.GPEvolutionMessage;
import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class GeneticInfo {
    private static final Logger Log = LoggerFactory.getLogger(GeneticInfo.class);
    private boolean geneticBuild;
    private GPFitnessEvolutionData[] islandsEvoData;

    public boolean isGeneticBuild() {
        return this.geneticBuild;
    }

    public GPFitnessEvolutionData[] getIslandsEvoData() {
        return this.islandsEvoData;
    }

    public void reset(boolean bl, int n) {
        this.geneticBuild = bl;
        if (this.geneticBuild) {
            this.islandsEvoData = new GPFitnessEvolutionData[n];
        }
    }

    public void update(GPEvolutionMessage gPEvolutionMessage) {
        if (gPEvolutionMessage.islandIndex < 0 || gPEvolutionMessage.islandIndex >= this.islandsEvoData.length) {
            return;
        }
        this.islandsEvoData[gPEvolutionMessage.islandIndex] = gPEvolutionMessage.fitnessEvolutionData;
    }
}

