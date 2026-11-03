/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.IGPNode;
import com.strategyquant.tradinglib.gp.ISelectionStrategy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RouletteWheelSelection<T extends IGPNode>
implements ISelectionStrategy<T> {
    public static final Logger Log = LoggerFactory.getLogger((String)"RouletteWheelSelection");

    @Override
    public <T extends IGPNode> List<T> select(List<T> list, boolean bl, int n, IRandomGenerator iRandomGenerator, List<T> list2) {
        double[] dArray = new double[list.size()];
        dArray[0] = this.getAdjustedFitness(((IGPNode)list.get(0)).getFitness((byte)11), bl);
        for (int i = 1; i < list.size(); ++i) {
            double d = this.getAdjustedFitness(((IGPNode)list.get(i)).getFitness((byte)11), bl);
            dArray[i] = dArray[i - 1] + d;
        }
        ArrayList<IGPNode> arrayList = new ArrayList<IGPNode>(n);
        for (int i = 0; i < n; ++i) {
            double d = iRandomGenerator.nextDouble() * dArray[dArray.length - 1];
            int n2 = Arrays.binarySearch(dArray, d);
            if (n2 < 0) {
                n2 = Math.abs(n2 + 1);
            }
            arrayList.add((IGPNode)list.get(n2));
        }
        return arrayList;
    }

    private double getAdjustedFitness(double d, boolean bl) {
        if (bl) {
            return d;
        }
        return d == 0.0 ? Double.POSITIVE_INFINITY : 1.0 / d;
    }

    private <T extends IGPNode> void printPopulation(String string, List<T> list) {
        Log.info("---------------------------------------------------------");
        Log.info("--- Text : " + string);
        Log.info("---------------------------------------------------------");
        for (int i = 0; i < list.size(); ++i) {
            IGPNode iGPNode = (IGPNode)list.get(i);
            Log.info("Candidate " + iGPNode.getAsString() + " - fitness: " + iGPNode.getFitness((byte)11));
        }
    }
}

