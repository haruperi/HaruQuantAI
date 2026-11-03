/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.gp.GPFitnessEvolutionData;
import java.io.Serializable;

public class GPEvolutionMessage
implements Serializable {
    public static final int InitialPopulationStarted = 10;
    public static final int InitialPopulationGenerated = 20;
    public static final int NewGeneration = 30;
    public static final int Finished = 40;
    public static final int InitialPopulationEvaluating = 50;
    public static final int RestartedAfterFinish = 60;
    public static final int RestartedAfterStagnation = 70;
    public static final int AdditionalPopulationStarted = 80;
    public static final int AdditionalPopulationEvaluating = 90;
    public static final int AdditionalPopulationGenerated = 100;
    public int messageType;
    public int currentGeneration;
    public int islandIndex;
    public String message;
    public int populationSize;
    public GPFitnessEvolutionData fitnessEvolutionData;

    public GPEvolutionMessage(int n, int n2, int n3, int n4, String string) {
        this.messageType = n;
        this.currentGeneration = n2;
        this.islandIndex = n3;
        this.populationSize = n4;
        this.message = string;
    }
}

