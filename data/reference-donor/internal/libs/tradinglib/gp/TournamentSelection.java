/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  com.strategyquant.lib.IRandomGenerator
 *  it.unimi.dsi.fastutil.objects.ObjectArrayList
 *  org.slf4j.Logger
 *  org.slf4j.LoggerFactory
 */
package com.strategyquant.tradinglib.gp;

import com.strategyquant.lib.IRandomGenerator;
import com.strategyquant.tradinglib.gp.GPFitnessComparator;
import com.strategyquant.tradinglib.gp.GPIDs;
import com.strategyquant.tradinglib.gp.IGPNode;
import com.strategyquant.tradinglib.gp.ISelectionStrategy;
import it.unimi.dsi.fastutil.objects.ObjectArrayList;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class TournamentSelection<T extends IGPNode>
implements ISelectionStrategy<T> {
    public static final Logger Log = LoggerFactory.getLogger((String)"TournamentSelection");
    private int tournamentSize = 3;
    private double tournamentProbability = 0.8;
    private GPFitnessComparator gpComparator = new GPFitnessComparator(false, 11);

    @Override
    public <T extends IGPNode> List<T> select(List<T> list, boolean bl, int n, IRandomGenerator iRandomGenerator, List<T> list2) {
        if (!bl) {
            throw new IllegalArgumentException("Not implemented for non-natural fitness");
        }
        return this.select2(list, bl, n, iRandomGenerator, list2);
    }

    public <T extends IGPNode> List<T> select2(List<T> list, boolean bl, int n, IRandomGenerator iRandomGenerator, List<T> list2) {
        ObjectArrayList objectArrayList = new ObjectArrayList();
        int n2 = (int)((double)n * 0.2);
        if (n2 > 15) {
            n2 = 10;
        }
        if (n2 > 20) {
            n2 /= 2;
        }
        ArrayList<T> arrayList = new ArrayList<T>(n);
        for (int i = 0; i < n; ++i) {
            int n3;
            T t = this.select(list, objectArrayList, iRandomGenerator);
            arrayList.add(t);
            int n4 = 0;
            for (n3 = 0; n3 < arrayList.size(); ++n3) {
                IGPNode iGPNode = (IGPNode)arrayList.get(n3);
                if (!iGPNode.getGPIDs().isSame(t.getGPIDs())) continue;
                ++n4;
            }
            n3 = 0;
            for (int j = 0; j < arrayList.size(); ++j) {
                IGPNode iGPNode = (IGPNode)arrayList.get(j);
                if (!iGPNode.getGPIDs().isSame(t.getGPIDs())) continue;
                ++n3;
            }
            if (n4 + n3 <= n2) continue;
            this.removeSameFromPopulation(t.getGPIDs(), list);
        }
        return arrayList;
    }

    private <T extends IGPNode> T removeSameFromPopulation(GPIDs gPIDs, List<T> list) {
        for (int i = 0; i < list.size(); ++i) {
            if (!gPIDs.isSame(((IGPNode)list.get(i)).getGPIDs()) || list.size() <= 2) continue;
            list.remove(i);
            --i;
        }
        return null;
    }

    private <T extends IGPNode> T select(List<T> list, ObjectArrayList<T> objectArrayList, IRandomGenerator iRandomGenerator) {
        int n;
        int n2 = list.size();
        objectArrayList.clear();
        for (n = 0; n < this.tournamentSize; ++n) {
            objectArrayList.add((Object)((IGPNode)list.get(iRandomGenerator.nextInt(n2))));
        }
        Collections.sort(objectArrayList, this.gpComparator);
        for (n = 1; n <= this.tournamentSize; ++n) {
            double d = iRandomGenerator.nextDouble();
            if (!(d < this.tournamentProbability)) continue;
            return (T)((IGPNode)objectArrayList.get(this.tournamentSize - n));
        }
        return (T)((IGPNode)objectArrayList.get(this.tournamentSize - 1));
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

