/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  com.strategyquant.lib.L
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.lib.L;
import com.strategyquant.tradinglib.gp.AbstractCrossover;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.optimization.OptimizationIndexes;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import java.util.ArrayList;
import java.util.List;

public class OptimizationIndexesCrossover
extends AbstractCrossover<OptimizationIndexes> {
    private OptimizationParams parameters;

    public OptimizationIndexesCrossover(OptimizationParams optimizationParams) {
        this(optimizationParams, 1);
    }

    public OptimizationIndexesCrossover(OptimizationParams optimizationParams, int n) {
        super(n);
        this.parameters = optimizationParams;
    }

    @Override
    protected List<OptimizationIndexes> mate(OptimizationIndexes optimizationIndexes, OptimizationIndexes optimizationIndexes2, int n, IRandomGenerator iRandomGenerator, int n2, int n3) {
        short[] sArray;
        short[] sArray2;
        short[] sArray3;
        short[] sArray4 = optimizationIndexes.getIndexes();
        if (sArray4.length != (sArray3 = optimizationIndexes.getIndexes()).length) {
            throw new IllegalArgumentException(L.tsq((String)"Cannot perform cross-over with different length parents."));
        }
        int n4 = 10;
        do {
            sArray2 = this.copyParent(sArray4);
            sArray = this.copyParent(sArray3);
            if (--n4 <= 0) break;
            for (int i = 0; i < n; ++i) {
                int n5 = 0;
                int n6 = 0;
                if (sArray4.length > 1) {
                    n5 = iRandomGenerator.nextInt(sArray4.length - 1);
                    n6 = n5 + iRandomGenerator.nextInt(sArray4.length - n5);
                }
                for (int j = n5; j <= n6; ++j) {
                    short s = sArray2[j];
                    sArray2[j] = sArray[j];
                    sArray[j] = s;
                }
            }
        } while (!this.checkCorrect(sArray2) || !this.checkCorrect(sArray));
        ArrayList<OptimizationIndexes> arrayList = new ArrayList<OptimizationIndexes>(2);
        arrayList.add(this.checkIsSameAndAdd(optimizationIndexes, optimizationIndexes2, sArray2, n2, n3));
        arrayList.add(this.checkIsSameAndAdd(optimizationIndexes2, optimizationIndexes, sArray, n2, n3));
        return arrayList;
    }

    private OptimizationIndexes checkIsSameAndAdd(OptimizationIndexes optimizationIndexes, OptimizationIndexes optimizationIndexes2, short[] sArray, int n, int n2) {
        if (optimizationIndexes.isSame(sArray)) {
            return optimizationIndexes;
        }
        OptimizationIndexes optimizationIndexes3 = new OptimizationIndexes(sArray);
        GPIDs gPIDs = new GPIDs();
        gPIDs.islandIndex = n;
        gPIDs.generationIndex = n2;
        gPIDs.generationType = "Crossover";
        gPIDs.parent1 = optimizationIndexes.getGPIDs().toShortString();
        gPIDs.parent2 = optimizationIndexes2.getGPIDs().toShortString();
        optimizationIndexes3.setGPIDs(gPIDs);
        return optimizationIndexes3;
    }

    private boolean checkCorrect(short[] sArray) {
        int n = 0;
        for (int i = 0; i < this.parameters.size(); ++i) {
            Parameter parameter = (Parameter)this.parameters.get(i);
            if (!parameter.isUsed()) continue;
            if (sArray[n] >= parameter.getCombinationsCount()) {
                return false;
            }
            ++n;
        }
        return true;
    }

    private short[] copyParent(short[] sArray) {
        short[] sArray2 = new short[sArray.length];
        for (int i = 0; i < sArray.length; ++i) {
            sArray2[i] = sArray[i];
        }
        return sArray2;
    }
}

