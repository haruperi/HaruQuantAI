/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.utils.ISQCloneable
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.utils.ISQCloneable;
import com.strategyquant.tradinglib.gp.GPGenerationTypes;

public class GPIDs
implements ISQCloneable<GPIDs> {
    public int islandIndex = -1;
    public int generationIndex = -1;
    public int nodeIndex = -1;
    public String generationType = GPGenerationTypes.Unknown;
    public String parent1 = null;
    public String parent2 = null;

    public GPIDs() {
    }

    public GPIDs(GPIDs gPIDs) {
        this.set(gPIDs);
    }

    public String toString() {
        if (this.generationType.equals("Mutation")) {
            return String.format("%d.%d.%d (%s from %s)", this.islandIndex + 1, this.generationIndex, this.nodeIndex, this.generationType, this.parent1);
        }
        if (this.generationType.equals("Crossover")) {
            return String.format("%d.%d.%d (%s from %s+%s)", this.islandIndex + 1, this.generationIndex, this.nodeIndex, this.generationType, this.parent1, this.parent2);
        }
        return String.format("%d.%d.%d (%s)", this.islandIndex + 1, this.generationIndex, this.nodeIndex, this.generationType);
    }

    public String toShortString() {
        return String.format("%d.%d.%d", this.islandIndex + 1, this.generationIndex, this.nodeIndex);
    }

    public void set(GPIDs gPIDs) {
        this.islandIndex = gPIDs.islandIndex;
        this.generationIndex = gPIDs.generationIndex;
        this.nodeIndex = gPIDs.nodeIndex;
        this.generationType = gPIDs.generationType;
        this.parent1 = gPIDs.parent1;
        this.parent2 = gPIDs.parent2;
    }

    public GPIDs getClone() throws Exception {
        GPIDs gPIDs = new GPIDs();
        gPIDs.islandIndex = this.islandIndex;
        gPIDs.generationIndex = this.generationIndex;
        gPIDs.nodeIndex = this.nodeIndex;
        gPIDs.generationType = this.generationType;
        gPIDs.parent1 = this.parent1;
        gPIDs.parent2 = this.parent2;
        return gPIDs;
    }

    public boolean isSame(GPIDs gPIDs) {
        if (gPIDs == null) {
            return false;
        }
        return this.islandIndex == gPIDs.islandIndex && this.generationIndex == gPIDs.generationIndex && this.nodeIndex == gPIDs.nodeIndex;
    }
}

