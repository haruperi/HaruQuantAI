/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 */
package com.strategyquant.tradinglib.optimization;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.AbstractFactory;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IEvolutionaryOperator;
import com.strategyquant.tradinglib.optimization.OptimizationIndexes;
import com.strategyquant.tradinglib.optimization.OptimizationParams;
import com.strategyquant.tradinglib.optimization.Parameter;
import java.util.ArrayList;
import java.util.List;

public class OptimizationIndexesMutation
implements IEvolutionaryOperator<OptimizationIndexes> {
    private OptimizationParams parameters;
    private final double mutationProbability;

    public OptimizationIndexesMutation(OptimizationParams optimizationParams, double d) {
        this.parameters = optimizationParams;
        this.mutationProbability = d;
    }

    @Override
    public List<OptimizationIndexes> apply(List<OptimizationIndexes> list, IRandomGenerator iRandomGenerator, AbstractFactory<OptimizationIndexes> abstractFactory, int n, int n2) throws Exception {
        ArrayList<OptimizationIndexes> arrayList = new ArrayList<OptimizationIndexes>(list.size());
        for (int i = 0; i < list.size(); ++i) {
            OptimizationIndexes optimizationIndexes = list.get(i);
            short[] sArray = optimizationIndexes.getIndexes();
            short[] sArray2 = this.mutate(sArray, iRandomGenerator);
            if (sArray2 != null) {
                OptimizationIndexes optimizationIndexes2 = new OptimizationIndexes(sArray2);
                GPIDs gPIDs = optimizationIndexes.getGPIDs();
                GPIDs gPIDs2 = new GPIDs();
                gPIDs2.islandIndex = n;
                gPIDs2.generationIndex = n2;
                gPIDs2.generationType = "Mutation";
                gPIDs2.parent1 = gPIDs != null ? gPIDs.toShortString() : "";
                optimizationIndexes2.setGPIDs(gPIDs2);
                arrayList.add(optimizationIndexes2);
                continue;
            }
            arrayList.add(optimizationIndexes);
        }
        return arrayList;
    }

    private short[] mutate(short[] sArray, IRandomGenerator iRandomGenerator) throws Exception {
        short[] sArray2 = new short[sArray.length];
        if (sArray == null) {
            return null;
        }
        boolean bl = false;
        for (int i = 0; i < sArray.length; ++i) {
            if (iRandomGenerator.probability(this.mutationProbability)) {
                sArray2[i] = (short)iRandomGenerator.nextInt(((Parameter)this.parameters.get(i)).getCombinationsCount());
                bl = true;
                continue;
            }
            sArray2[i] = sArray[i];
        }
        if (bl) {
            return sArray2;
        }
        return null;
    }
}

