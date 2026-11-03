/*
 * Decompiled with CFR 0.152.
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.tradinglib.gp.IGPNode;
import java.io.Serializable;
import java.util.ArrayList;

public class GPEvolutionPopulationMessage<T extends IGPNode>
implements Serializable {
    public int currentGeneration;
    public int islandIndex;
    public ArrayList<T> population;

    public GPEvolutionPopulationMessage(int n, int n2, ArrayList<T> arrayList) {
        this.currentGeneration = n;
        this.islandIndex = n2;
        this.population = arrayList;
    }
}

